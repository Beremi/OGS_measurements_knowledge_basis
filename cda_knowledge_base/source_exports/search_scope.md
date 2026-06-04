# Gmail Search Scope

The Gmail scan used searches for Gesa, the named collaborators, and BGR TeamBeam transfers related to CD-A/HERMES.

## Direct Sender Searches

| Query | Result |
| --- | --- |
| `from:Gesa.Ziefle@bgr.de` | 30 messages found. |
| `from:Tuanny.Cajuhi@bgr.de` | 2 messages found. |
| `from:Kristof.Kessler@bgr.de` | No direct sender messages found. |
| `from:Stephan.Costabel@bgr.de` | 1 message found. |
| `from:Markus.Furche@bgr.de` | No direct sender messages found. |
| `from:Herbert.Kunz@bgr.de` | No direct sender messages found. |
| `from:Jobst.Massmann@bgr.de` | No direct sender messages found. |
| `from:Bastian.Graupner@ensi.ch` | No direct sender messages found. |
| `from:no-reply@teambeam.bgr.de gesa` | 7 TeamBeam notification messages found. |

## Mention Searches

| Query | Result |
| --- | --- |
| `"Kristof.Kessler@bgr.de"` | Found in Gesa/TeamBeam messages around the model/container transfer. |
| `"Markus.Furche@bgr.de"` | Found in ERT and meeting-related messages. |
| `"Herbert.Kunz@bgr.de"` | Found in meeting-related messages. |
| `"Jobst.Massmann@bgr.de"` | Found in meeting-related messages. |
| `"Bastian.Graupner@ensi.ch"` | Found in Gesa's collaboration/meeting messages. |
| `from:no-reply@teambeam.bgr.de CD-A` | 7 TeamBeam messages found. |
| `from:no-reply@teambeam.bgr.de HERMES` | 6 TeamBeam messages found. |
| `from:no-reply@teambeam.bgr.de Ziefle` | 1 TeamBeam message found. |

## Limitations

- TeamBeam message bodies expose file names, sizes, hashes, links, and expiry dates, but not the file contents.
- Gmail attachment download succeeded for common document/data formats such as PDF, PPTX, XLSX, TXT, ICS, PNG, JPG, and DAT.
- Gmail connector download did not work for some raw/archive formats such as `.zip`, `.ohm`, and `.tx0`; those files were later recovered from the local Thunderbird mail store.
- The scan focused on CD-A/HERMES modelling relevance. Non-CD-A mailbox material was intentionally not summarized.
