import collections
import re

from XLMMacroDeobfuscator.deobfuscator import process_file
from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import Result, ResultSection

from pattern_match import PatternMatch


def get_result_subsection(result, title, heuristic):
    result_subsection = None
    # Set appropriate result subsection if it already exists
    for subsection in result.subsections:
        if subsection.title_text == title:
            result_subsection = subsection
    # Create appropriate result subsection if it doesn't already exist
    if not result_subsection:
        result_subsection = ResultSection(title)
        result.add_subsection(result_subsection)
        result_subsection.set_heuristic(heuristic)
    return result_subsection


def tag_data(data, data_deobfuscated, result_ioc, result_formula):
    pattern = PatternMatch()

    # Get all IoCs without deobfuscation
    ioc_dict = {}
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
    ioc_deobfuscated_dict = {}
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
            pattern = re.compile('(\\n|^)' + re.escape(ioc) + '(\\n|$)')
            if ioc_subsection.body is not None and not pattern.search(ioc_subsection.body):
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
            pattern = re.compile('(\\n|^)' + re.escape(ioc) + '(\\n|$)')
            if ioc_subsection.body is not None and not pattern.search(ioc_subsection.body):
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


def add_results(result, data, data_deobfuscated):
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
    def start(self):
        self.log.info('XLM Macro Deobfuscator service started')

    def stop(self):
        self.log.info('XLM Macro Deobfuscator service ended')

    def execute(self, request):
        result = Result()
        request.result = result
        file_path = request.file_path
        password = request.get_param('password')
        start_point = request.get_param('start point')

        data = process_file(file=file_path,
                            password=password,
                            noninteractive=True,
                            no_indent=True,
                            output_level=0,
                            return_deobfuscated=True,
                            extract_only=True)

        data_deobfuscated = process_file(file=file_path,
                                         password=password,
                                         start_point=start_point,
                                         noninteractive=True,
                                         no_indent=True,
                                         output_level=0,
                                         output_formula_format='[[CELL-ADDR]]: [[INT-FORMULA]]',
                                         return_deobfuscated=True)

        add_results(result, data, data_deobfuscated)
