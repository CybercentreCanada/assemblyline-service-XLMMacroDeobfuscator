ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH xlm_macro_deobfuscator.XLMMacroDeobfuscator

# Get latest version of XLMMacroDeobfuscator library and dependencies
RUN pip install -U https://github.com/DissectMalware/xlrd2/archive/master.zip
RUN pip install -U https://github.com/DissectMalware/pyxlsb2/archive/master.zip
RUN pip install -U https://github.com/DissectMalware/XLMMacroDeobfuscator/archive/master.zip

# Optional dependencies
RUN pip install -U defusedxml

# Switch to assemblyline user
USER assemblyline

# Copy Result service code
WORKDIR /opt/al_service
COPY . .

# Patch version in manifest
ARG version=4.0.0.dev1
USER root
RUN sed -i -e "s/\$SERVICE_TAG/$version/g" service_manifest.yml

# Switch to assemblyline user
USER assemblyline
