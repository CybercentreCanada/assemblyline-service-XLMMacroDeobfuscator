ARG branch=latest
FROM cccs/assemblyline-v4-service-base:$branch

ENV SERVICE_PATH xlm_macro_deobfuscator.XLMMacroDeobfuscator

# Install XLMMacroDeobfuscator library and optional dependencies
RUN pip install -U xlmmacrodeobfuscator defusedxml

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
