import collections
import json
import os
import re
import tempfile
from subprocess import run
from typing import Dict, List, Optional, Set, Tuple

# Use global silent configuration
import XLMMacroDeobfuscator.configs.settings as settings
from assemblyline.common import forge
from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.request import ServiceRequest
from assemblyline_v4_service.common.result import Result, ResultSection
from XLMMacroDeobfuscator_.pattern_match import PatternMatch

settings.SILENT = True

# Import after setting SILENT because SILENT is suppress optional import warnings
from XLMMacroDeobfuscator.deobfuscator import process_file  # noqa: E402

IDENTIFY = forge.get_identify(use_cache=os.environ.get("PRIVILEGED", "false").lower() == "true")

def get_result_subsection(result: ResultSection, title: str, heuristic: int) -> ResultSection:
    """ Gets the subsection with the given title or creates it if it doesn't exist """
    # Set appropriate result subsection if it already exists
    for subsection in result.subsections:
        if subsection.title_text == title:
            result_subsection = subsection
            break
    # Create appropriate result subsection if it doesn't already exist
    else:
        result_subsection = ResultSection(title)
        result.add_subsection(result_subsection)
        result_subsection.set_heuristic(heuristic)
    return result_subsection


def tag_data(data: List[str], data_deobfuscated: List[str], result_ioc: ResultSection,
             result_formula: ResultSection) -> None:
    pattern = PatternMatch()

    # Get all IoCs without deobfuscation
    ioc_dict: Dict[str, Set[Tuple[str, str, int, str]]] = {}
    formulas = collections.OrderedDict()
    for line in data:
        if line[:4] == 'CELL':
            split_value = line.split(',', 1)
            cell = split_value[0].split(':')[1].strip()
            formula = split_value[1].rsplit(',', 1)[0].strip()

            # Add formula to list of formulas if it contains IoC(s)
            if pattern.ioc_match(formula, cell, ioc_dict):
                formulas[cell] = formula

    # Get all IoCs after deobfuscation
    ioc_deobfuscated_dict: Dict[str, Set[Tuple[str, str, int, str]]] = {}
    formulas_deobfuscated = collections.OrderedDict()
    for line in data_deobfuscated:
        split_value = line.split(':', 1)
        cell = split_value[0].strip()
        formula = split_value[1].strip()

        # Add formula to list of deobfuscated formulas if it contains IoC(s)
        if pattern.ioc_match(formula, cell, ioc_deobfuscated_dict):
            formulas_deobfuscated[cell] = formula

    # Remove duplicate IoCs (found both before AND after deobfuscation)
    for ioc_tag, values in ioc_deobfuscated_dict.copy().items():
        for ioc_details in values.copy():
            if ioc_tag in ioc_dict and ioc_details in ioc_dict[ioc_tag]:
                ioc_deobfuscated_dict[ioc_tag].remove(ioc_details)
                # Remove ioc_tag if no IoCs are associated with it
                if len(ioc_deobfuscated_dict[ioc_tag]) == 0:
                    del ioc_deobfuscated_dict[ioc_tag]

    # Remove duplicate formulas from the same cell (found both before AND after deobfuscation)
    for cell, formula in formulas_deobfuscated.copy().items():
        if cell in formulas and formula in formulas[cell]:
            del formulas_deobfuscated[cell]

    # Create the appropriate result subsections for formulas
    formulas_subsection = ResultSection('Formulas')
    formulas_deobfuscated_subsection = ResultSection('Deobfuscated Formulas')
    formulas_deobfuscated_subsection.set_heuristic(5)
    if formulas:
        result_formula.add_subsection(formulas_subsection)
    if formulas_deobfuscated:
        result_formula.add_subsection(formulas_deobfuscated_subsection)

    # Generate result subsections for IoCs found without deobfuscation
    heuristics = [1, 2]
    for ioc_tag, values in ioc_dict.items():
        for ioc_details in values:
            ioc = ioc_details[0]
            title = ioc_details[1]
            heuristic = heuristics[ioc_details[2]]

            ioc_subsection = get_result_subsection(result_ioc, title, heuristic)
            ioc_subsection.add_tag(ioc_tag, ioc)
            if ioc_subsection.body is not None \
                    and not re.search('(\\n|^)' + re.escape(ioc) + '(\\n|$)', ioc_subsection.body):
                ioc_subsection.add_line(ioc)
            elif ioc_subsection.body is None:
                ioc_subsection.add_line(ioc)

            formulas_subsection.add_tag(ioc_tag, ioc)

    # Generate result subsections for deobfuscated IoCs
    heuristics = [3, 4]
    for ioc_tag, values in ioc_deobfuscated_dict.items():
        for ioc_details in values:
            ioc = ioc_details[0]
            title = 'Deobfuscated ' + ioc_details[1]
            heuristic = heuristics[ioc_details[2]]

            ioc_subsection = get_result_subsection(result_ioc, title, heuristic)
            ioc_subsection.add_tag(ioc_tag, ioc)
            if ioc_subsection.body is not None \
                    and not re.search('(\\n|^)' + re.escape(ioc) + '(\\n|$)', ioc_subsection.body):
                ioc_subsection.add_line(ioc)
            elif ioc_subsection.body is None:
                ioc_subsection.add_line(ioc)

            formulas_deobfuscated_subsection.add_tag(ioc_tag, ioc)

    # Populate 'Formulas' result subsection with all suspicious formulas found without deobfuscation
    for cell, formula in formulas.items():
        # Only add complete formulas
        if "FORMULA(" in formula:
            cell_referenced = formula.rsplit(',', 1)[1][:-1]
            if cell_referenced not in formulas.keys():
                formulas_subsection.add_line(cell + ": " + formula)
        else:
            formulas_subsection.add_line(cell + ": " + formula)

    # Populate 'Deobfuscated Formulas' result subsection with all deobfuscated suspicious formulas
    for cell, formula in formulas_deobfuscated.items():
        # Only add complete formulas
        if "FORMULA(" in formula:
            cell_referenced = formula.rsplit(',', 1)[1][:-1]
            if cell_referenced not in formulas_deobfuscated.keys():
                formulas_deobfuscated_subsection.add_line(cell + ": " + formula)
        else:
            formulas_deobfuscated_subsection.add_line(cell + ": " + formula)


def add_results(result: Result, data: List[str], data_deobfuscated: List[str]) -> None:
    result_ioc = ResultSection('Found the following IoCs')
    result_formula = ResultSection('Suspicious formulas found in document')

    # Tag IoCs/formulas and generate result subsections
    tag_data(data, data_deobfuscated, result_ioc, result_formula)

    # Add 'IoCs' result section to results if IoCs were found
    if result_ioc.subsections:
        result.add_section(result_ioc)
    # Add 'Suspicious Formulas' result section to results if suspicious formulas were found
    if result_formula.subsections:
        result.add_section(result_formula)


class XLMMacroDeobfuscator(ServiceBase):

    DEOBS_FORMULAS_FILE = 'deobfuscated_formulas.txt'

    def __init__(self, config: Optional[Dict] = None):
        self.use_CLI = False
        super().__init__(config)

    def start(self) -> None:
        self.log.info('XLM Macro Deobfuscator service started')
        self.use_CLI = self.config.get('use_CLI', False)

    def stop(self) -> None:
        self.log.info('XLM Macro Deobfuscator service ended')

    def execute(self, request: ServiceRequest) -> None:
        result = Result()
        request.result = result
        if IDENTIFY.fileinfo(request.file_path, generate_hashes=False, skip_fuzzy_hashes=True, calculate_entropy=False)['mime'] == "application/x-ole-storage":
            # Not a real excel file, skip processing
            return
        file_path = request.file_path
        start_point = request.get_param('start point')
        get_results = self.results_from_module

        if self.use_CLI:
            self.log.info('Using CLI method')
            get_results = self.results_from_CLI

        data, data_deobfuscated = get_results(file_path, start_point, request)

        if data_deobfuscated:
            deobs_path = os.path.join(self.working_directory, self.DEOBS_FORMULAS_FILE)
            try:
                with open(deobs_path, 'w') as f:
                    f.write('\n'.join(data_deobfuscated))
                request.add_supplementary(deobs_path, self.DEOBS_FORMULAS_FILE, 'Deobfuscated XLM fomulas')
            except Exception as e:
                self.log.warning(f'Could not add deobfuscated formulas for {request.file_name}: {str(e)}')

        if data or data_deobfuscated:
            add_results(result, data, data_deobfuscated)

    def results_from_CLI(self, file_path: str, start_point: str,
                         request: ServiceRequest) -> Tuple[List[str], List[str]]:
        data, data_deobfuscated = [], []

        def call_CLI(config: dict) -> Dict:
            config_file_name = None
            output_name = None

            try:
                # Create tempfiles
                config_file_fd, config_file_name = tempfile.mkstemp()
                output_fd, output_name = tempfile.mkstemp()

                with os.fdopen(config_file_fd, "w+t") as config_file:
                    config['export_json'] = output_name
                    json.dump(config, config_file)

                proc = run(['xlmdeobfuscator', f'-c={config_file_name}'], capture_output=True, check=False)

                trace = "\n".join(proc.stdout.decode().split('\n')[22:])
                # Check stdout, stderr for logging purposes
                error = False
                if proc.stderr:
                    self.log.error(proc.stderr)
                    error = True
                if 'error' in trace.lower():
                    self.log.error(f"Error detected in CLI output: {trace}")
                    error = True
                try:
                    with os.fdopen(output_fd, "r") as output:
                        return json.load(output)
                except json.JSONDecodeError:
                    if not error:
                        self.log.error('No output written on success.')
                    return {}
            finally:
                if config_file_name and os.path.exists(config_file_name):
                    os.unlink(config_file_name)
                if output_name and os.path.exists(output_name):
                    os.unlink(output_name)

        common_config = {
            "file": file_path,
            "noninteractive": True,
            "no_indent": True,
            "output_level": 0,
        }

        # Get results
        data_config = common_config.copy()
        data_config.update({'extract_only': True, "return_deobfuscated": True})

        deob_config = common_config.copy()

        data_json = call_CLI(data_config)
        deob_json = call_CLI(deob_config)

        # Attempt to parse results in List format as given from results_from_module output
        for record in data_json.get('records', []):
            if record.get('cell_add', False):
                data.append(f"CELL:{record['cell_add']} , {record['formula']} , {record['value']}")
        for record in deob_json.get('records', []):
            if record.get('cell_add', False):
                data_deobfuscated.append(f"{record['cell_add']}: {record['formula']}")

        return data, data_deobfuscated

    def results_from_module(self, file_path: str, start_point: str,
                            request: ServiceRequest) -> Tuple[List[str], List[str]]:
        data, data_deobfuscated = [], []
        try:
            data = process_file(file=file_path,
                                noninteractive=True,
                                no_indent=True,
                                output_level=0,
                                silent=True,
                                return_deobfuscated=True,
                                extract_only=True)

            data_deobfuscated = process_file(file=file_path,
                                             start_point=start_point,
                                             noninteractive=True,
                                             no_indent=True,
                                             output_level=0,
                                             silent=True,
                                             output_formula_format='[[CELL-ADDR]]: [[INT-FORMULA]]',
                                             return_deobfuscated=True)
        except Exception as e:
            self.log.error(e)
            section = ResultSection('Failed to analyze', parent=request.result)
            section.add_line(str(e))
            if str(e).startswith('Failed to decrypt'):
                section.set_heuristic(6)
        return data, data_deobfuscated
