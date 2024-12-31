[![Discord](https://img.shields.io/badge/chat-on%20discord-7289da.svg?sanitize=true)](https://discord.gg/GUAy9wErNu)
[![](https://img.shields.io/discord/908084610158714900)](https://discord.gg/GUAy9wErNu)
[![Static Badge](https://img.shields.io/badge/github-assemblyline-blue?logo=github)](https://github.com/CybercentreCanada/assemblyline)
[![Static Badge](https://img.shields.io/badge/github-assemblyline_service_XLMMacroDeobfuscator-blue?logo=github)](https://github.com/CybercentreCanada/assemblyline-service-XLMMacroDeobfuscator)
[![GitHub Issues or Pull Requests by label](https://img.shields.io/github/issues/CybercentreCanada/assemblyline/service-XLMMacroDeobfuscator)](https://github.com/CybercentreCanada/assemblyline/issues?q=is:issue+is:open+label:service-XLMMacroDeobfuscator)
[![License](https://img.shields.io/github/license/CybercentreCanada/assemblyline-service-XLMMacroDeobfuscator)](./LICENSE)

# XLMMacroDeobfuscator Service

This services decodes obfuscated XLM macros (also known as Excel 4.0 macros).

## Service Details

This service wraps the excellent tool [XLMMacroDeobfuscator](https://github.com/DissectMalware/XLMMacroDeobfuscator) published by DissectMalware which utilizes an internal XLM emulator to interpret the macros, without fully performing the code.

Original license for the library can be found [here](https://github.com/DissectMalware/XLMMacroDeobfuscator/blob/master/LICENSE).

Thank you [@DissectMalware](https://github.com/DissectMalware) for releasing this tool!

## Image variants and tags

Assemblyline services are built from the [Assemblyline service base image](https://hub.docker.com/r/cccs/assemblyline-v4-service-base),
which is based on Debian 11 with Python 3.11.

Assemblyline services use the following tag definitions:

| **Tag Type** | **Description**                                                                                  |      **Example Tag**       |
| :----------: | :----------------------------------------------------------------------------------------------- | :------------------------: |
|    latest    | The most recent build (can be unstable).                                                         |          `latest`          |
|  build_type  | The type of build used. `dev` is the latest unstable build. `stable` is the latest stable build. |     `stable` or `dev`      |
|    series    | Complete build details, including version and build type: `version.buildType`.                   | `4.5.stable`, `4.5.1.dev3` |

## Running this service

This is an Assemblyline service. It is designed to run as part of the Assemblyline framework.

If you would like to test this service locally, you can run the Docker image directly from the a shell:

    docker run \
        --name Xlmmacrodeobfuscator \
        --env SERVICE_API_HOST=http://`ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -f1 -d"/"`:5003 \
        --network=host \
        cccs/assemblyline-service-XLMMacroDeobfuscator

To add this service to your Assemblyline deployment, follow this
[guide](https://cybercentrecanada.github.io/assemblyline4_docs/developer_manual/services/run_your_service/#add-the-container-to-your-deployment).

## Documentation

General Assemblyline documentation can be found at: https://cybercentrecanada.github.io/assemblyline4_docs/

# Service XLMMacroDeobfuscator

Ce service décode les macros XLM obfusquées (également connues sous le nom de macros Excel 4.0).

## Détails du service

Ce service intègre l'excellent outil [XLMMacroDeobfuscator](https://github.com/DissectMalware/XLMMacroDeobfuscator) publié par DissectMalware qui utilise un émulateur XLM interne pour interpréter les macros, sans exécuter complètement le code.

La licence originale de la bibliothèque peut être trouvée [ici](https://github.com/DissectMalware/XLMMacroDeobfuscator/blob/master/LICENSE).

Merci à [@DissectMalware](https://github.com/DissectMalware) d'avoir publié cet outil!

## Variantes et étiquettes d'image

Les services d'Assemblyline sont construits à partir de l'image de base [Assemblyline service](https://hub.docker.com/r/cccs/assemblyline-v4-service-base),
qui est basée sur Debian 11 avec Python 3.11.

Les services d'Assemblyline utilisent les définitions d'étiquettes suivantes:

| **Type d'étiquette** | **Description**                                                                                                |  **Exemple d'étiquette**   |
| :------------------: | :------------------------------------------------------------------------------------------------------------- | :------------------------: |
|   dernière version   | La version la plus récente (peut être instable).                                                               |          `latest`          |
|      build_type      | Type de construction utilisé. `dev` est la dernière version instable. `stable` est la dernière version stable. |     `stable` ou `dev`      |
|        série         | Détails de construction complets, comprenant la version et le type de build: `version.buildType`.              | `4.5.stable`, `4.5.1.dev3` |

## Exécution de ce service

Ce service est spécialement optimisé pour fonctionner dans le cadre d'un déploiement d'Assemblyline.

Si vous souhaitez tester ce service localement, vous pouvez exécuter l'image Docker directement à partir d'un terminal:

    docker run \
        --name Xlmmacrodeobfuscator \
        --env SERVICE_API_HOST=http://`ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -f1 -d"/"`:5003 \
        --network=host \
        cccs/assemblyline-service-XLMMacroDeobfuscator

Pour ajouter ce service à votre déploiement d'Assemblyline, suivez ceci
[guide](https://cybercentrecanada.github.io/assemblyline4_docs/fr/developer_manual/services/run_your_service/#add-the-container-to-your-deployment).

## Documentation

La documentation générale sur Assemblyline peut être consultée à l'adresse suivante: https://cybercentrecanada.github.io/assemblyline4_docs/
