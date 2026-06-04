# Deep Source Pass: Model Projection Inputs

This generated file records the detailed pass through copied source files in this measurement folder.
It is meant for fast orientation; the raw files in `source_files/` remain the authoritative data.

## Source Files

### 2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip

- Local copy: [2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip](../../source_files/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip)
- Type: `zip`; size: 1912962 bytes
- SHA1: `9373d37e1ac2480d2449c465975dc79cea505ad9`
- Original/raw provenance candidates: cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip
- ZIP members: 28; uncompressed bytes: 5183105
- ZIP extension counts: .pptx=1; .prj=1; .pvsm=1; .py=1; .txt=1; .vtu=8; .xml=15
- ZIP member CSV: [zip_member_deep_summary.csv](zip_member_deep_summary.csv)
- Keyword hits: CD-A; niche
- First extracted lines / sheet headers: 01_processes_TRM.xml | 02_process_variables_TRM.xml | 03_parameters_TRM.xml | 03_parameters_TRM_orig.xml | 04_1_media_aqu_liq.xml | 04_2_media_twophase.xml | 04_media_TRM.xml | 05_1_fixed_timestepping.xml | 05_time_loop_TRM.xml | 06_nonlinear_solver_T.xml

### CDA_N4_2D_250403.zip

- Local copy: [CDA_N4_2D_250403.zip](../../source_files/CDA_N4_2D_250403.zip)
- Type: `zip`; size: 1067122 bytes
- SHA1: `c3f859449d58591a3452c6e374cacf5b43e3cd05`
- Original/raw provenance candidates: cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip
- ZIP members: 22; uncompressed bytes: 3368601
- ZIP extension counts: .prj=1; .vtu=7; .xml=14
- ZIP member CSV: [zip_member_deep_summary.csv](zip_member_deep_summary.csv)
- Keyword hits: CD-A; niche
- First extracted lines / sheet headers: CDA_N4_2D_250403/01_processes_TRM.xml | CDA_N4_2D_250403/02_process_variables_TRM.xml | CDA_N4_2D_250403/03_parameters_TRM.xml | CDA_N4_2D_250403/04_1_media_aqu_liq.xml | CDA_N4_2D_250403/04_2_media_twophase.xml | CDA_N4_2D_250403/04_media_TRM.xml | CDA_N4_2D_250403/05_1_fixed_timestepping.xml | CDA_N4_2D_250403/05_time_loop_TRM.xml | CDA_N4_2D_250403/06_nonlinear_solver_T.xml | CDA_N4_2D_250403/07_linear_solver_T.xml

### 01_processes_TRM.xml

- Local copy: [01_processes_TRM.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/01_processes_TRM.xml)
- Type: `text/data`; size: 1613 bytes
- SHA1: `848b5757431ad0d9323f74baf5845ca6c167cefa`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/01_processes_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::01_processes_TRM.xml
- Searchable extract/outline: [01_processes_TRM_26bca93f.xml.head.txt](extracted_text/01_processes_TRM_26bca93f.xml.head.txt)
- Text/data line count: 34
- Keyword hits: saturation; pressure
- First extracted lines / sheet headers: <process> | <name>TRM</name> | <type>THERMO_RICHARDS_MECHANICS</type> | <integration_order>4</integration_order> | <!-- <dimension>2</dimension> --> | <!-- Gestein --> | <constitutive_relation id="0"> | <type>LinearElasticOrthotropic</type> | <youngs_moduli>E</youngs_moduli> | <shear_moduli>G</shear_moduli>

### 02_process_variables_TRM.xml

- Local copy: [02_process_variables_TRM.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/02_process_variables_TRM.xml)
- Type: `text/data`; size: 2378 bytes
- SHA1: `90e20c5ee5cf2f0ae1e9ee64458dbcb891ef5e13`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/02_process_variables_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::02_process_variables_TRM.xml
- Searchable extract/outline: [02_process_variables_TRM_36c4d34d.xml.head.txt](extracted_text/02_process_variables_TRM_36c4d34d.xml.head.txt)
- Text/data line count: 73
- Keyword hits: pressure; CD-A; niche
- First extracted lines / sheet headers: <process_variable> | <name>displacement</name> | <components>2</components> | <order>2</order> | <initial_condition>ic_displacement</initial_condition> | <boundary_conditions> | <boundary_condition> | <mesh>cd-a_left</mesh> | <type>Dirichlet</type> | <component>0</component>

### 03_parameters_TRM.xml

- Local copy: [03_parameters_TRM.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/03_parameters_TRM.xml)
- Type: `text/data`; size: 5601 bytes
- SHA1: `ff7c284ae234350b8d86e52cb788a00adb86cc70`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/03_parameters_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::03_parameters_TRM.xml
- Searchable extract/outline: [03_parameters_TRM_b1305ec4.xml.head.txt](extracted_text/03_parameters_TRM_b1305ec4.xml.head.txt)
- Text/data line count: 183
- Keyword hits: pressure; niche
- First extracted lines / sheet headers: <!-- IC --> | <parameter> | <name>ic_displacement</name> | <type>Constant</type> | <values>0 0</values> | <!--type>MeshNode</type> | <field_name>displacement</field_name--> | </parameter> | <parameter> | <name>ic_pressure</name> <!-- check pressure0 + ic_sigma0 -->

### 04_1_media_aqu_liq.xml

- Local copy: [04_1_media_aqu_liq.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/04_1_media_aqu_liq.xml)
- Type: `text/data`; size: 2880 bytes
- SHA1: `8ba341270221506ef3b5deb94a3d7a9730515498`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_1_media_aqu_liq.xml
- Searchable extract/outline: [04_1_media_aqu_liq_cf22ea90.xml.head.txt](extracted_text/04_1_media_aqu_liq_cf22ea90.xml.head.txt)
- Text/data line count: 78
- Keyword hits: ERT; pressure
- First extracted lines / sheet headers: <phase> | <type>AqueousLiquid</type> | <properties> | <property> | <name>specific_heat_capacity</name> | <type>Parameter</type> | <parameter_name>c_p_l</parameter_name> | </property> | <property> | <name>thermal_conductivity</name>

### 04_2_media_twophase.xml

- Local copy: [04_2_media_twophase.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/04_2_media_twophase.xml)
- Type: `text/data`; size: 792 bytes
- SHA1: `a57c40add0a8d37c39ba7c716063f7e6c5bc01a9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_2_media_twophase.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_2_media_twophase.xml
- Searchable extract/outline: [04_2_media_twophase_85bc321c.xml.head.txt](extracted_text/04_2_media_twophase_85bc321c.xml.head.txt)
- Text/data line count: 23
- Keyword hits: ERT; permeability; saturation
- First extracted lines / sheet headers: <property> | <name>relative_permeability</name> | <type>RelativePermeabilityVanGenuchten</type> | <residual_liquid_saturation>0.1</residual_liquid_saturation> | <residual_gas_saturation>0</residual_gas_saturation> | <exponent>0.45</exponent> | <minimum_relative_permeability_liquid>1e-25</minimum_relative_permeability_liquid> | </property> | <property> | <name>saturation</name>

### 04_media_TRM.xml

- Local copy: [04_media_TRM.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/04_media_TRM.xml)
- Type: `text/data`; size: 1950 bytes
- SHA1: `6b68ab641d97eeeadd965d73417ab4b645d4ffd2`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_media_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_media_TRM.xml
- Searchable extract/outline: [04_media_TRM_efa5fb27.xml.head.txt](extracted_text/04_media_TRM_efa5fb27.xml.head.txt)
- Text/data line count: 72
- Keyword hits: ERT; permeability; saturation; pressure; OGS
- First extracted lines / sheet headers: <!-- | Parameter, die in Ogs5 vorhanden waren, welche in Ogs6 bisher aber noch zu fehlen scheinen oder | nicht mehr benötigt werden: | PERMEABILITY_SATURATION | CAPILLARY_PRESSURE | STORAGE | --> | <medium id="0,1"><!--,2,3,4,6,7,8,9,11,12,13,14"--> | <properties> | <property>

### 05_1_fixed_timestepping.xml

- Local copy: [05_1_fixed_timestepping.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/05_1_fixed_timestepping.xml)
- Type: `text/data`; size: 2144 bytes
- SHA1: `aa32f810c195d02a47c5b5faa3901547912c93d7`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_1_fixed_timestepping.xml
- Searchable extract/outline: [05_1_fixed_timestepping_e715e671.xml.head.txt](extracted_text/05_1_fixed_timestepping_e715e671.xml.head.txt)
- Text/data line count: 40
- First extracted lines / sheet headers: <time_stepping> | <type>FixedTimeStepping</type> | <t_initial>0</t_initial><!-- last time step --> | <t_end>140000000</t_end><!-- last time step of the curve --> | <!--t_initial>3153624278400</t_initial--><!-- last time step --> | <!--t_end>3153759099264</t_end--><!-- last time step of the curve --> | <timesteps> | <pair> | <repeat>365</repeat> | <delta_t>86400</delta_t><!--1 day-->

### 05_time_loop_TRM.xml

- Local copy: [05_time_loop_TRM.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/05_time_loop_TRM.xml)
- Type: `text/data`; size: 1835 bytes
- SHA1: `106cb755797f3d5cc956e5102195247ce884c165`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_time_loop_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_time_loop_TRM.xml
- Searchable extract/outline: [05_time_loop_TRM_b0af82dd.xml.head.txt](extracted_text/05_time_loop_TRM_b0af82dd.xml.head.txt)
- Text/data line count: 49
- Keyword hits: saturation; pressure; CD-A
- First extracted lines / sheet headers: <processes> | <process ref="TRM"> | <nonlinear_solver>basic_newton</nonlinear_solver> | <!--compensate_non_equilibrium_initial_residuum>true | </compensate_non_equilibrium_initial_residuum--> | <convergence_criterion> | <type>PerComponentDeltaX</type> | <norm_type>NORM2</norm_type> | <abstols>1e-10 1e-10 1e-10 1e-10</abstols> | <reltols>1e-8 1e-8 1e-8 1e-8</reltols>

### 06_nonlinear_solver_T.xml

- Local copy: [06_nonlinear_solver_T.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/06_nonlinear_solver_T.xml)
- Type: `text/data`; size: 185 bytes
- SHA1: `4ba846b864d87d955f03c67a79aafd4c94a410e1`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::06_nonlinear_solver_T.xml
- Searchable extract/outline: [06_nonlinear_solver_T_43d22917.xml.head.txt](extracted_text/06_nonlinear_solver_T_43d22917.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <nonlinear_solver> | <name>basic_newton</name> | <type>Newton</type> | <max_iter>150</max_iter> | <linear_solver>general_linear_solver</linear_solver> | </nonlinear_solver>

### 07_linear_solver_T.xml

- Local copy: [07_linear_solver_T.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/07_linear_solver_T.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `56d3a8bb2867a99d0027597ef4e76e3e769b67d5`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/07_linear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::07_linear_solver_T.xml
- Searchable extract/outline: [07_linear_solver_T_df04b4f3.xml.head.txt](extracted_text/07_linear_solver_T_df04b4f3.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <linear_solver> | <name>general_linear_solver</name> | <eigen> | <solver_type>PardisoLU</solver_type> | </eigen> | </linear_solver>

### 08_08_open_niche_seasonal.xml

- Local copy: [08_08_open_niche_seasonal.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/08_08_open_niche_seasonal.xml)
- Type: `text/data`; size: 35319 bytes
- SHA1: `235d07fa789046e0875b00e11583561a5d3a7910`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_08_open_niche_seasonal.xml
- Searchable extract/outline: [08_08_open_niche_seasonal_b0035ecc.xml.head.txt](extracted_text/08_08_open_niche_seasonal_b0035ecc.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>0.0 159740.3603603579 319480.72072071955 479221.0810810812 638961.4414414391 798701.8018018007 958442.1621621624 1118182.5225225203 1277922.882882882 1437663.2432432398 1597403.6036036015 1757143.963963963 1916884.324324321 2076624.6846846826 2236365.0450450443 2396105.405405402 2555845.765765764 2715586.1261261255 2875326.4864864834 3035066.846846845 3194807.2072072066 3354547.5675675645 3514287.927927926 3674028.288288288 3833768.6486486457 3993509.0090090074 4153249.369369369 4312989.729729727 4472730.090090089 4632470.45045045 4792210.810810808 4951951.17117117 5111691.531531531 5271431.891891889 5431172.252252251 5590912.612612613 5750652.97297297 5910393.333333332 6070133.693693694 6229874.054054052 6389614.414414413 6549354.774774775 6709095.135135133 6868835.495495494 7028575.855855852 7188316.216216214 7348056.576576576 7507796.93...

### 08_curves.xml

- Local copy: [08_curves.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/08_curves.xml)
- Type: `text/data`; size: 223 bytes
- SHA1: `d39fe15825540b8e805cbf6a81e953c62a9eeab9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_curves.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_curves.xml
- Searchable extract/outline: [08_curves_6e2ecbc7.xml.head.txt](extracted_text/08_curves_6e2ecbc7.xml.head.txt)
- Text/data line count: 10
- Keyword hits: niche
- First extracted lines / sheet headers: <curve> | <include file="./08_08_open_niche_seasonal.xml" /> <!--open_niche_seasonal_curve_shifted.xml" /--> | </curve> | <!-- | <curve> | <include file="./closed_niche_seasonal_curve_shifted.xml" /> | </curve> | -->

### bulk.vtu

- Local copy: [bulk.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/bulk.vtu)
- Type: `vtu`; size: 1380973 bytes
- SHA1: `9a15c579914caab9012638f36af674ba7566a886`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::bulk.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/bulk.vtu

### bulk_all.vtu

- Local copy: [bulk_all.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/bulk_all.vtu)
- Type: `vtu`; size: 1834288 bytes
- SHA1: `d77258e31b0c11e1d06e603d301c2767ce126241`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::bulk_all.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/bulk_all.vtu

### cd-a_bottom.vtu

- Local copy: [cd-a_bottom.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd-a_bottom.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `53cd9e66076feb90da8cea5dde6f402ec85d0677`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_bottom.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_bottom.vtu

### cd-a_left.vtu

- Local copy: [cd-a_left.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd-a_left.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `b6806808e3d17d91d571329e5466841cb64ed1ae`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_left.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_left.vtu

### cd-a_niche4.vtu

- Local copy: [cd-a_niche4.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd-a_niche4.vtu)
- Type: `vtu`; size: 45643 bytes
- SHA1: `a27fa6ec2498321ee861b2e11891da96159b6d9d`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_niche4.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_niche4.vtu

### cd-a_right.vtu

- Local copy: [cd-a_right.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd-a_right.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `678a306075bc04384fc7c935b5f137d2725bf171`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_right.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_right.vtu

### cd-a_top.vtu

- Local copy: [cd-a_top.vtu](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd-a_top.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `3aecdaa221e9e78b748ad6b2abb734ecf8b1a7df`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_top.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_top.vtu

### cd_a_open_niche_quad.prj

- Local copy: [cd_a_open_niche_quad.prj](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/cd_a_open_niche_quad.prj)
- Type: `text/data`; size: 1072 bytes
- SHA1: `a83fa8708ba5da7b3a0aad2b80e1dca329148217`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/cd_a_open_niche_quad.prj; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd_a_open_niche_quad.prj; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd_a_open_niche_quad.prj
- Searchable extract/outline: [cd_a_open_niche_quad_05ecb4d5.prj.head.txt](extracted_text/cd_a_open_niche_quad_05ecb4d5.prj.head.txt)
- Text/data line count: 38
- Keyword hits: CD-A; niche
- First extracted lines / sheet headers: <?xml version="1.0" encoding="ISO-8859-1"?> | <OpenGeoSysProject> | <meshes> | <mesh>bulk.vtu</mesh> | <mesh>bulk_all.vtu</mesh> | <mesh>cd-a_niche4.vtu</mesh> | <mesh>cd-a_left.vtu</mesh> | <mesh>cd-a_right.vtu</mesh> | <mesh>cd-a_top.vtu</mesh> | <mesh>cd-a_bottom.vtu</mesh>

### closed_niche_seasonal_curve_shifted.xml

- Local copy: [closed_niche_seasonal_curve_shifted.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/closed_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `f126b5892d086319af536f698e293a0306da2075`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::closed_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [closed_niche_seasonal_curve_shifted_15152805.xml.head.txt](extracted_text/closed_niche_seasonal_curve_shifted_15152805.xml.head.txt)
- Text/data line count: 3
- Keyword hits: niche
- First extracted lines / sheet headers: <name>closed_niche_seasonal_curve</name> | <coords>3153624278400.0 3153764278400.0</coords> | <values>116080.57942975157 116080.57942975157</values>

### open_niche_seasonal_curve_shifted.xml

- Local copy: [open_niche_seasonal_curve_shifted.xml](../../source_files/CDA_N4_2D_250403/CDA_N4_2D_250403/open_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 33881 bytes
- SHA1: `a306b331492c6da66796b4875f68f1b92f5c0af3`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::open_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [open_niche_seasonal_curve_shifted_0b418c71.xml.head.txt](extracted_text/open_niche_seasonal_curve_shifted_0b418c71.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>3153624278400.0 3153624438140.3604 3153624597880.7207 3153624757621.081 3153624917361.4414 3153625077101.802 3153625236842.162 3153625396582.5225 3153625556322.883 3153625716063.243 3153625875803.6035 3153626035543.964 3153626195284.324 3153626355024.6846 3153626514765.045 3153626674505.4053 3153626834245.7656 3153626993986.126 3153627153726.4863 3153627313466.8467 3153627473207.207 3153627632947.5674 3153627792687.9277 3153627952428.288 3153628112168.6484 3153628271909.009 3153628431649.369 3153628591389.7295 3153628751130.0903 3153628910870.4507 3153629070610.811 3153629230351.1714 3153629390091.5317 3153629549831.892 3153629709572.2524 3153629869312.613 3153630029052.973 3153630188793.3335 3153630348533.694 3153630508274.054 3153630668014.4146 3153630827754.775 3153630987495.1353 3153631147235.4956 3153631306975.856 3153631466716.2163 3...

### CDA_N4_2D_250509.zip

- Local copy: [CDA_N4_2D_250509.zip](../../source_files/CDA_N4_2D_250509.zip)
- Type: `zip`; size: 35680 bytes
- SHA1: `1747d6c44371f0b0b0af7836a1169f9646dd7eba`
- Original/raw provenance candidates: cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip
- ZIP members: 14; uncompressed bytes: 89381
- ZIP extension counts: .xml=14
- ZIP member CSV: [zip_member_deep_summary.csv](zip_member_deep_summary.csv)
- Keyword hits: niche
- First extracted lines / sheet headers: 01_processes_TRM.xml | 02_process_variables_TRM.xml | 03_parameters_TRM.xml | 04_1_media_aqu_liq.xml | 04_2_media_twophase.xml | 04_media_TRM.xml | 05_1_fixed_timestepping.xml | 05_time_loop_TRM.xml | 06_nonlinear_solver_T.xml | 07_linear_solver_T.xml

### 01_processes_TRM.xml

- Local copy: [01_processes_TRM.xml](../../source_files/CDA_N4_2D_250509/01_processes_TRM.xml)
- Type: `text/data`; size: 1613 bytes
- SHA1: `848b5757431ad0d9323f74baf5845ca6c167cefa`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/01_processes_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::01_processes_TRM.xml
- Searchable extract/outline: [01_processes_TRM_86b6f1b0.xml.head.txt](extracted_text/01_processes_TRM_86b6f1b0.xml.head.txt)
- Text/data line count: 34
- Keyword hits: saturation; pressure
- First extracted lines / sheet headers: <process> | <name>TRM</name> | <type>THERMO_RICHARDS_MECHANICS</type> | <integration_order>4</integration_order> | <!-- <dimension>2</dimension> --> | <!-- Gestein --> | <constitutive_relation id="0"> | <type>LinearElasticOrthotropic</type> | <youngs_moduli>E</youngs_moduli> | <shear_moduli>G</shear_moduli>

### 02_process_variables_TRM.xml

- Local copy: [02_process_variables_TRM.xml](../../source_files/CDA_N4_2D_250509/02_process_variables_TRM.xml)
- Type: `text/data`; size: 2378 bytes
- SHA1: `90e20c5ee5cf2f0ae1e9ee64458dbcb891ef5e13`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/02_process_variables_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::02_process_variables_TRM.xml
- Searchable extract/outline: [02_process_variables_TRM_6a2f107e.xml.head.txt](extracted_text/02_process_variables_TRM_6a2f107e.xml.head.txt)
- Text/data line count: 73
- Keyword hits: pressure; CD-A; niche
- First extracted lines / sheet headers: <process_variable> | <name>displacement</name> | <components>2</components> | <order>2</order> | <initial_condition>ic_displacement</initial_condition> | <boundary_conditions> | <boundary_condition> | <mesh>cd-a_left</mesh> | <type>Dirichlet</type> | <component>0</component>

### 03_parameters_TRM.xml

- Local copy: [03_parameters_TRM.xml](../../source_files/CDA_N4_2D_250509/03_parameters_TRM.xml)
- Type: `text/data`; size: 5601 bytes
- SHA1: `ff7c284ae234350b8d86e52cb788a00adb86cc70`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/03_parameters_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::03_parameters_TRM.xml
- Searchable extract/outline: [03_parameters_TRM_31cc588c.xml.head.txt](extracted_text/03_parameters_TRM_31cc588c.xml.head.txt)
- Text/data line count: 183
- Keyword hits: pressure; niche
- First extracted lines / sheet headers: <!-- IC --> | <parameter> | <name>ic_displacement</name> | <type>Constant</type> | <values>0 0</values> | <!--type>MeshNode</type> | <field_name>displacement</field_name--> | </parameter> | <parameter> | <name>ic_pressure</name> <!-- check pressure0 + ic_sigma0 -->

### 04_1_media_aqu_liq.xml

- Local copy: [04_1_media_aqu_liq.xml](../../source_files/CDA_N4_2D_250509/04_1_media_aqu_liq.xml)
- Type: `text/data`; size: 2880 bytes
- SHA1: `8ba341270221506ef3b5deb94a3d7a9730515498`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_1_media_aqu_liq.xml
- Searchable extract/outline: [04_1_media_aqu_liq_8474c4bc.xml.head.txt](extracted_text/04_1_media_aqu_liq_8474c4bc.xml.head.txt)
- Text/data line count: 78
- Keyword hits: ERT; pressure
- First extracted lines / sheet headers: <phase> | <type>AqueousLiquid</type> | <properties> | <property> | <name>specific_heat_capacity</name> | <type>Parameter</type> | <parameter_name>c_p_l</parameter_name> | </property> | <property> | <name>thermal_conductivity</name>

### 04_2_media_twophase.xml

- Local copy: [04_2_media_twophase.xml](../../source_files/CDA_N4_2D_250509/04_2_media_twophase.xml)
- Type: `text/data`; size: 792 bytes
- SHA1: `a57c40add0a8d37c39ba7c716063f7e6c5bc01a9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_2_media_twophase.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_2_media_twophase.xml
- Searchable extract/outline: [04_2_media_twophase_7888d7eb.xml.head.txt](extracted_text/04_2_media_twophase_7888d7eb.xml.head.txt)
- Text/data line count: 23
- Keyword hits: ERT; permeability; saturation
- First extracted lines / sheet headers: <property> | <name>relative_permeability</name> | <type>RelativePermeabilityVanGenuchten</type> | <residual_liquid_saturation>0.1</residual_liquid_saturation> | <residual_gas_saturation>0</residual_gas_saturation> | <exponent>0.45</exponent> | <minimum_relative_permeability_liquid>1e-25</minimum_relative_permeability_liquid> | </property> | <property> | <name>saturation</name>

### 04_media_TRM.xml

- Local copy: [04_media_TRM.xml](../../source_files/CDA_N4_2D_250509/04_media_TRM.xml)
- Type: `text/data`; size: 1950 bytes
- SHA1: `6b68ab641d97eeeadd965d73417ab4b645d4ffd2`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_media_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_media_TRM.xml
- Searchable extract/outline: [04_media_TRM_855a2e0c.xml.head.txt](extracted_text/04_media_TRM_855a2e0c.xml.head.txt)
- Text/data line count: 72
- Keyword hits: ERT; permeability; saturation; pressure; OGS
- First extracted lines / sheet headers: <!-- | Parameter, die in Ogs5 vorhanden waren, welche in Ogs6 bisher aber noch zu fehlen scheinen oder | nicht mehr benötigt werden: | PERMEABILITY_SATURATION | CAPILLARY_PRESSURE | STORAGE | --> | <medium id="0,1"><!--,2,3,4,6,7,8,9,11,12,13,14"--> | <properties> | <property>

### 05_1_fixed_timestepping.xml

- Local copy: [05_1_fixed_timestepping.xml](../../source_files/CDA_N4_2D_250509/05_1_fixed_timestepping.xml)
- Type: `text/data`; size: 2354 bytes
- SHA1: `6deeb611eee6d8d7f90c61de431ccaa579c4582a`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_1_fixed_timestepping.xml
- Searchable extract/outline: [05_1_fixed_timestepping_6d38d5a6.xml.head.txt](extracted_text/05_1_fixed_timestepping_6d38d5a6.xml.head.txt)
- Text/data line count: 44
- First extracted lines / sheet headers: <time_stepping> | <type>FixedTimeStepping</type> | <t_initial>0</t_initial><!-- last time step --> | <t_end>140000000</t_end><!-- last time step of the curve --> | <!--t_initial>3153624278400</t_initial--><!-- last time step --> | <!--t_end>3153759099264</t_end--><!-- last time step of the curve --> | <timesteps> | <pair> | <repeat>365</repeat> | <delta_t>864000</delta_t><!--t0 = 18.09.2019; deltat= 10d so that first output is exported at the end of the month -->

### 05_time_loop_TRM.xml

- Local copy: [05_time_loop_TRM.xml](../../source_files/CDA_N4_2D_250509/05_time_loop_TRM.xml)
- Type: `text/data`; size: 1913 bytes
- SHA1: `9aeebe19310aad9fc2d096a1439648efaa214240`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_time_loop_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_time_loop_TRM.xml
- Searchable extract/outline: [05_time_loop_TRM_f325f4ec.xml.head.txt](extracted_text/05_time_loop_TRM_f325f4ec.xml.head.txt)
- Text/data line count: 49
- Keyword hits: ERT; saturation; pressure; CD-A
- First extracted lines / sheet headers: <processes> | <process ref="TRM"> | <nonlinear_solver>basic_newton</nonlinear_solver> | <!--compensate_non_equilibrium_initial_residuum>true | </compensate_non_equilibrium_initial_residuum--> | <convergence_criterion> | <type>PerComponentDeltaX</type> | <norm_type>NORM2</norm_type> | <abstols>1e-10 1e-10 1e-10 1e-10</abstols> | <reltols>1e-8 1e-8 1e-8 1e-8</reltols>

### 06_nonlinear_solver_T.xml

- Local copy: [06_nonlinear_solver_T.xml](../../source_files/CDA_N4_2D_250509/06_nonlinear_solver_T.xml)
- Type: `text/data`; size: 185 bytes
- SHA1: `4ba846b864d87d955f03c67a79aafd4c94a410e1`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::06_nonlinear_solver_T.xml
- Searchable extract/outline: [06_nonlinear_solver_T_ae2de936.xml.head.txt](extracted_text/06_nonlinear_solver_T_ae2de936.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <nonlinear_solver> | <name>basic_newton</name> | <type>Newton</type> | <max_iter>150</max_iter> | <linear_solver>general_linear_solver</linear_solver> | </nonlinear_solver>

### 07_linear_solver_T.xml

- Local copy: [07_linear_solver_T.xml](../../source_files/CDA_N4_2D_250509/07_linear_solver_T.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `56d3a8bb2867a99d0027597ef4e76e3e769b67d5`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/07_linear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::07_linear_solver_T.xml
- Searchable extract/outline: [07_linear_solver_T_cd2c6aa3.xml.head.txt](extracted_text/07_linear_solver_T_cd2c6aa3.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <linear_solver> | <name>general_linear_solver</name> | <eigen> | <solver_type>PardisoLU</solver_type> | </eigen> | </linear_solver>

### 08_08_open_niche_seasonal.xml

- Local copy: [08_08_open_niche_seasonal.xml](../../source_files/CDA_N4_2D_250509/08_08_open_niche_seasonal.xml)
- Type: `text/data`; size: 35319 bytes
- SHA1: `235d07fa789046e0875b00e11583561a5d3a7910`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_08_open_niche_seasonal.xml
- Searchable extract/outline: [08_08_open_niche_seasonal_59a2b98e.xml.head.txt](extracted_text/08_08_open_niche_seasonal_59a2b98e.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>0.0 159740.3603603579 319480.72072071955 479221.0810810812 638961.4414414391 798701.8018018007 958442.1621621624 1118182.5225225203 1277922.882882882 1437663.2432432398 1597403.6036036015 1757143.963963963 1916884.324324321 2076624.6846846826 2236365.0450450443 2396105.405405402 2555845.765765764 2715586.1261261255 2875326.4864864834 3035066.846846845 3194807.2072072066 3354547.5675675645 3514287.927927926 3674028.288288288 3833768.6486486457 3993509.0090090074 4153249.369369369 4312989.729729727 4472730.090090089 4632470.45045045 4792210.810810808 4951951.17117117 5111691.531531531 5271431.891891889 5431172.252252251 5590912.612612613 5750652.97297297 5910393.333333332 6070133.693693694 6229874.054054052 6389614.414414413 6549354.774774775 6709095.135135133 6868835.495495494 7028575.855855852 7188316.216216214 7348056.576576576 7507796.93...

### 08_curves.xml

- Local copy: [08_curves.xml](../../source_files/CDA_N4_2D_250509/08_curves.xml)
- Type: `text/data`; size: 223 bytes
- SHA1: `d39fe15825540b8e805cbf6a81e953c62a9eeab9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_curves.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_curves.xml
- Searchable extract/outline: [08_curves_ea72cb75.xml.head.txt](extracted_text/08_curves_ea72cb75.xml.head.txt)
- Text/data line count: 10
- Keyword hits: niche
- First extracted lines / sheet headers: <curve> | <include file="./08_08_open_niche_seasonal.xml" /> <!--open_niche_seasonal_curve_shifted.xml" /--> | </curve> | <!-- | <curve> | <include file="./closed_niche_seasonal_curve_shifted.xml" /> | </curve> | -->

### closed_niche_seasonal_curve_shifted.xml

- Local copy: [closed_niche_seasonal_curve_shifted.xml](../../source_files/CDA_N4_2D_250509/closed_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `f126b5892d086319af536f698e293a0306da2075`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::closed_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [closed_niche_seasonal_curve_shifted_d89e8f16.xml.head.txt](extracted_text/closed_niche_seasonal_curve_shifted_d89e8f16.xml.head.txt)
- Text/data line count: 3
- Keyword hits: niche
- First extracted lines / sheet headers: <name>closed_niche_seasonal_curve</name> | <coords>3153624278400.0 3153764278400.0</coords> | <values>116080.57942975157 116080.57942975157</values>

### open_niche_seasonal_curve_shifted.xml

- Local copy: [open_niche_seasonal_curve_shifted.xml](../../source_files/CDA_N4_2D_250509/open_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 33881 bytes
- SHA1: `a306b331492c6da66796b4875f68f1b92f5c0af3`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::open_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [open_niche_seasonal_curve_shifted_db2a549d.xml.head.txt](extracted_text/open_niche_seasonal_curve_shifted_db2a549d.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>3153624278400.0 3153624438140.3604 3153624597880.7207 3153624757621.081 3153624917361.4414 3153625077101.802 3153625236842.162 3153625396582.5225 3153625556322.883 3153625716063.243 3153625875803.6035 3153626035543.964 3153626195284.324 3153626355024.6846 3153626514765.045 3153626674505.4053 3153626834245.7656 3153626993986.126 3153627153726.4863 3153627313466.8467 3153627473207.207 3153627632947.5674 3153627792687.9277 3153627952428.288 3153628112168.6484 3153628271909.009 3153628431649.369 3153628591389.7295 3153628751130.0903 3153628910870.4507 3153629070610.811 3153629230351.1714 3153629390091.5317 3153629549831.892 3153629709572.2524 3153629869312.613 3153630029052.973 3153630188793.3335 3153630348533.694 3153630508274.054 3153630668014.4146 3153630827754.775 3153630987495.1353 3153631147235.4956 3153631306975.856 3153631466716.2163 3...

### long_report.tex

- Local copy: [long_report.tex](../../source_files/SOTA_OGS_Mont_Terri_zip/long_report.tex)
- Type: `tex`; size: 51227 bytes
- SHA1: `2dafec4dd75075fc4b8e2f92e653d2f6846971c1`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::long_report.tex

### main.tex

- Local copy: [main.tex](../../source_files/SOTA_OGS_Mont_Terri_zip/main.tex)
- Type: `tex`; size: 25438 bytes
- SHA1: `455f8497af0bbf4bfb6daceb6db6545de03de9dd`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::main.tex

### 01_processes_TRM.xml

- Local copy: [01_processes_TRM.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/01_processes_TRM.xml)
- Type: `text/data`; size: 1613 bytes
- SHA1: `848b5757431ad0d9323f74baf5845ca6c167cefa`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/01_processes_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::01_processes_TRM.xml
- Searchable extract/outline: [01_processes_TRM_010e46ce.xml.head.txt](extracted_text/01_processes_TRM_010e46ce.xml.head.txt)
- Text/data line count: 34
- Keyword hits: saturation; pressure
- First extracted lines / sheet headers: <process> | <name>TRM</name> | <type>THERMO_RICHARDS_MECHANICS</type> | <integration_order>4</integration_order> | <!-- <dimension>2</dimension> --> | <!-- Gestein --> | <constitutive_relation id="0"> | <type>LinearElasticOrthotropic</type> | <youngs_moduli>E</youngs_moduli> | <shear_moduli>G</shear_moduli>

### 02_process_variables_TRM.xml

- Local copy: [02_process_variables_TRM.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/02_process_variables_TRM.xml)
- Type: `text/data`; size: 2378 bytes
- SHA1: `90e20c5ee5cf2f0ae1e9ee64458dbcb891ef5e13`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/02_process_variables_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::02_process_variables_TRM.xml
- Searchable extract/outline: [02_process_variables_TRM_8bf6fae4.xml.head.txt](extracted_text/02_process_variables_TRM_8bf6fae4.xml.head.txt)
- Text/data line count: 73
- Keyword hits: pressure; CD-A; niche
- First extracted lines / sheet headers: <process_variable> | <name>displacement</name> | <components>2</components> | <order>2</order> | <initial_condition>ic_displacement</initial_condition> | <boundary_conditions> | <boundary_condition> | <mesh>cd-a_left</mesh> | <type>Dirichlet</type> | <component>0</component>

### 03_parameters_TRM.xml

- Local copy: [03_parameters_TRM.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/03_parameters_TRM.xml)
- Type: `text/data`; size: 5601 bytes
- SHA1: `ff7c284ae234350b8d86e52cb788a00adb86cc70`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/03_parameters_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::03_parameters_TRM.xml
- Searchable extract/outline: [03_parameters_TRM_6f2e5720.xml.head.txt](extracted_text/03_parameters_TRM_6f2e5720.xml.head.txt)
- Text/data line count: 183
- Keyword hits: pressure; niche
- First extracted lines / sheet headers: <!-- IC --> | <parameter> | <name>ic_displacement</name> | <type>Constant</type> | <values>0 0</values> | <!--type>MeshNode</type> | <field_name>displacement</field_name--> | </parameter> | <parameter> | <name>ic_pressure</name> <!-- check pressure0 + ic_sigma0 -->

### 04_1_media_aqu_liq.xml

- Local copy: [04_1_media_aqu_liq.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/04_1_media_aqu_liq.xml)
- Type: `text/data`; size: 2880 bytes
- SHA1: `8ba341270221506ef3b5deb94a3d7a9730515498`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_1_media_aqu_liq.xml
- Searchable extract/outline: [04_1_media_aqu_liq_56d88b52.xml.head.txt](extracted_text/04_1_media_aqu_liq_56d88b52.xml.head.txt)
- Text/data line count: 78
- Keyword hits: ERT; pressure
- First extracted lines / sheet headers: <phase> | <type>AqueousLiquid</type> | <properties> | <property> | <name>specific_heat_capacity</name> | <type>Parameter</type> | <parameter_name>c_p_l</parameter_name> | </property> | <property> | <name>thermal_conductivity</name>

### 04_2_media_twophase.xml

- Local copy: [04_2_media_twophase.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/04_2_media_twophase.xml)
- Type: `text/data`; size: 792 bytes
- SHA1: `a57c40add0a8d37c39ba7c716063f7e6c5bc01a9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_2_media_twophase.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_2_media_twophase.xml
- Searchable extract/outline: [04_2_media_twophase_e7b5f7b0.xml.head.txt](extracted_text/04_2_media_twophase_e7b5f7b0.xml.head.txt)
- Text/data line count: 23
- Keyword hits: ERT; permeability; saturation
- First extracted lines / sheet headers: <property> | <name>relative_permeability</name> | <type>RelativePermeabilityVanGenuchten</type> | <residual_liquid_saturation>0.1</residual_liquid_saturation> | <residual_gas_saturation>0</residual_gas_saturation> | <exponent>0.45</exponent> | <minimum_relative_permeability_liquid>1e-25</minimum_relative_permeability_liquid> | </property> | <property> | <name>saturation</name>

### 04_media_TRM.xml

- Local copy: [04_media_TRM.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/04_media_TRM.xml)
- Type: `text/data`; size: 1950 bytes
- SHA1: `6b68ab641d97eeeadd965d73417ab4b645d4ffd2`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_media_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_media_TRM.xml
- Searchable extract/outline: [04_media_TRM_83f25a72.xml.head.txt](extracted_text/04_media_TRM_83f25a72.xml.head.txt)
- Text/data line count: 72
- Keyword hits: ERT; permeability; saturation; pressure; OGS
- First extracted lines / sheet headers: <!-- | Parameter, die in Ogs5 vorhanden waren, welche in Ogs6 bisher aber noch zu fehlen scheinen oder | nicht mehr benötigt werden: | PERMEABILITY_SATURATION | CAPILLARY_PRESSURE | STORAGE | --> | <medium id="0,1"><!--,2,3,4,6,7,8,9,11,12,13,14"--> | <properties> | <property>

### 05_1_fixed_timestepping.xml

- Local copy: [05_1_fixed_timestepping.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/05_1_fixed_timestepping.xml)
- Type: `text/data`; size: 2354 bytes
- SHA1: `6deeb611eee6d8d7f90c61de431ccaa579c4582a`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_1_fixed_timestepping.xml
- Searchable extract/outline: [05_1_fixed_timestepping_0e9a3477.xml.head.txt](extracted_text/05_1_fixed_timestepping_0e9a3477.xml.head.txt)
- Text/data line count: 44
- First extracted lines / sheet headers: <time_stepping> | <type>FixedTimeStepping</type> | <t_initial>0</t_initial><!-- last time step --> | <t_end>140000000</t_end><!-- last time step of the curve --> | <!--t_initial>3153624278400</t_initial--><!-- last time step --> | <!--t_end>3153759099264</t_end--><!-- last time step of the curve --> | <timesteps> | <pair> | <repeat>365</repeat> | <delta_t>864000</delta_t><!--t0 = 18.09.2019; deltat= 10d so that first output is exported at the end of the month -->

### 05_time_loop_TRM.xml

- Local copy: [05_time_loop_TRM.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/05_time_loop_TRM.xml)
- Type: `text/data`; size: 1913 bytes
- SHA1: `9aeebe19310aad9fc2d096a1439648efaa214240`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_time_loop_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_time_loop_TRM.xml
- Searchable extract/outline: [05_time_loop_TRM_c2bf5ae1.xml.head.txt](extracted_text/05_time_loop_TRM_c2bf5ae1.xml.head.txt)
- Text/data line count: 49
- Keyword hits: ERT; saturation; pressure; CD-A
- First extracted lines / sheet headers: <processes> | <process ref="TRM"> | <nonlinear_solver>basic_newton</nonlinear_solver> | <!--compensate_non_equilibrium_initial_residuum>true | </compensate_non_equilibrium_initial_residuum--> | <convergence_criterion> | <type>PerComponentDeltaX</type> | <norm_type>NORM2</norm_type> | <abstols>1e-10 1e-10 1e-10 1e-10</abstols> | <reltols>1e-8 1e-8 1e-8 1e-8</reltols>

### 06_nonlinear_solver_T.xml

- Local copy: [06_nonlinear_solver_T.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/06_nonlinear_solver_T.xml)
- Type: `text/data`; size: 185 bytes
- SHA1: `4ba846b864d87d955f03c67a79aafd4c94a410e1`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::06_nonlinear_solver_T.xml
- Searchable extract/outline: [06_nonlinear_solver_T_839b93f3.xml.head.txt](extracted_text/06_nonlinear_solver_T_839b93f3.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <nonlinear_solver> | <name>basic_newton</name> | <type>Newton</type> | <max_iter>150</max_iter> | <linear_solver>general_linear_solver</linear_solver> | </nonlinear_solver>

### 07_linear_solver_T.xml

- Local copy: [07_linear_solver_T.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/07_linear_solver_T.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `56d3a8bb2867a99d0027597ef4e76e3e769b67d5`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/07_linear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::07_linear_solver_T.xml
- Searchable extract/outline: [07_linear_solver_T_336874da.xml.head.txt](extracted_text/07_linear_solver_T_336874da.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <linear_solver> | <name>general_linear_solver</name> | <eigen> | <solver_type>PardisoLU</solver_type> | </eigen> | </linear_solver>

### 08_08_open_niche_seasonal.xml

- Local copy: [08_08_open_niche_seasonal.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/08_08_open_niche_seasonal.xml)
- Type: `text/data`; size: 35319 bytes
- SHA1: `235d07fa789046e0875b00e11583561a5d3a7910`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_08_open_niche_seasonal.xml
- Searchable extract/outline: [08_08_open_niche_seasonal_c4f1ab06.xml.head.txt](extracted_text/08_08_open_niche_seasonal_c4f1ab06.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>0.0 159740.3603603579 319480.72072071955 479221.0810810812 638961.4414414391 798701.8018018007 958442.1621621624 1118182.5225225203 1277922.882882882 1437663.2432432398 1597403.6036036015 1757143.963963963 1916884.324324321 2076624.6846846826 2236365.0450450443 2396105.405405402 2555845.765765764 2715586.1261261255 2875326.4864864834 3035066.846846845 3194807.2072072066 3354547.5675675645 3514287.927927926 3674028.288288288 3833768.6486486457 3993509.0090090074 4153249.369369369 4312989.729729727 4472730.090090089 4632470.45045045 4792210.810810808 4951951.17117117 5111691.531531531 5271431.891891889 5431172.252252251 5590912.612612613 5750652.97297297 5910393.333333332 6070133.693693694 6229874.054054052 6389614.414414413 6549354.774774775 6709095.135135133 6868835.495495494 7028575.855855852 7188316.216216214 7348056.576576576 7507796.93...

### 08_curves.xml

- Local copy: [08_curves.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/08_curves.xml)
- Type: `text/data`; size: 223 bytes
- SHA1: `d39fe15825540b8e805cbf6a81e953c62a9eeab9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_curves.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_curves.xml
- Searchable extract/outline: [08_curves_8593469f.xml.head.txt](extracted_text/08_curves_8593469f.xml.head.txt)
- Text/data line count: 10
- Keyword hits: niche
- First extracted lines / sheet headers: <curve> | <include file="./08_08_open_niche_seasonal.xml" /> <!--open_niche_seasonal_curve_shifted.xml" /--> | </curve> | <!-- | <curve> | <include file="./closed_niche_seasonal_curve_shifted.xml" /> | </curve> | -->

### cd_a_open_niche_quad.prj

- Local copy: [cd_a_open_niche_quad.prj](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/cd_a_open_niche_quad.prj)
- Type: `text/data`; size: 1072 bytes
- SHA1: `a83fa8708ba5da7b3a0aad2b80e1dca329148217`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/cd_a_open_niche_quad.prj; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd_a_open_niche_quad.prj; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd_a_open_niche_quad.prj
- Searchable extract/outline: [cd_a_open_niche_quad_d7e1e2aa.prj.head.txt](extracted_text/cd_a_open_niche_quad_d7e1e2aa.prj.head.txt)
- Text/data line count: 38
- Keyword hits: CD-A; niche
- First extracted lines / sheet headers: <?xml version="1.0" encoding="ISO-8859-1"?> | <OpenGeoSysProject> | <meshes> | <mesh>bulk.vtu</mesh> | <mesh>bulk_all.vtu</mesh> | <mesh>cd-a_niche4.vtu</mesh> | <mesh>cd-a_left.vtu</mesh> | <mesh>cd-a_right.vtu</mesh> | <mesh>cd-a_top.vtu</mesh> | <mesh>cd-a_bottom.vtu</mesh>

### closed_niche_seasonal_curve_shifted.xml

- Local copy: [closed_niche_seasonal_curve_shifted.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/closed_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `f126b5892d086319af536f698e293a0306da2075`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::closed_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [closed_niche_seasonal_curve_shifted_5cfd71ff.xml.head.txt](extracted_text/closed_niche_seasonal_curve_shifted_5cfd71ff.xml.head.txt)
- Text/data line count: 3
- Keyword hits: niche
- First extracted lines / sheet headers: <name>closed_niche_seasonal_curve</name> | <coords>3153624278400.0 3153764278400.0</coords> | <values>116080.57942975157 116080.57942975157</values>

### open_niche_seasonal_curve_shifted.xml

- Local copy: [open_niche_seasonal_curve_shifted.xml](../../source_files/SOTA_OGS_Mont_Terri_zip/ogs_settings/open_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 33881 bytes
- SHA1: `a306b331492c6da66796b4875f68f1b92f5c0af3`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::open_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [open_niche_seasonal_curve_shifted_75062d63.xml.head.txt](extracted_text/open_niche_seasonal_curve_shifted_75062d63.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>3153624278400.0 3153624438140.3604 3153624597880.7207 3153624757621.081 3153624917361.4414 3153625077101.802 3153625236842.162 3153625396582.5225 3153625556322.883 3153625716063.243 3153625875803.6035 3153626035543.964 3153626195284.324 3153626355024.6846 3153626514765.045 3153626674505.4053 3153626834245.7656 3153626993986.126 3153627153726.4863 3153627313466.8467 3153627473207.207 3153627632947.5674 3153627792687.9277 3153627952428.288 3153628112168.6484 3153628271909.009 3153628431649.369 3153628591389.7295 3153628751130.0903 3153628910870.4507 3153629070610.811 3153629230351.1714 3153629390091.5317 3153629549831.892 3153629709572.2524 3153629869312.613 3153630029052.973 3153630188793.3335 3153630348533.694 3153630508274.054 3153630668014.4146 3153630827754.775 3153630987495.1353 3153631147235.4956 3153631306975.856 3153631466716.2163 3...

### opalinus_clay.bib

- Local copy: [opalinus_clay.bib](../../source_files/SOTA_OGS_Mont_Terri_zip/opalinus_clay.bib)
- Type: `bib`; size: 4170 bytes
- SHA1: `af5f47e6dd30462307ce820f03c48cfcc18771b2`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::opalinus_clay.bib

### wang_kosakoeski_kolditz_thm_2009.pdf

- Local copy: [wang_kosakoeski_kolditz_thm_2009.pdf](../../source_files/SOTA_OGS_Mont_Terri_zip/wang_kosakoeski_kolditz_thm_2009.pdf)
- Type: `pdf`; size: 982106 bytes
- SHA1: `df31bfdbcb43d981828aae773c2f7374a328d0ce`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::wang_kosakoeski_kolditz_thm_2009.pdf
- Searchable extract/outline: [wang_kosakoeski_kolditz_thm_2009_d06f15f3.pdf.txt](extracted_text/wang_kosakoeski_kolditz_thm_2009_d06f15f3.pdf.txt)
- PDF pages: 11; extracted text characters: 55504
- Keyword hits: ERT; humidity; permeability; fracture; saturation; pressure
- First extracted lines / sheet headers: --- Page 1 --- | A parallel ﬁnite element scheme for thermo-hydro-mechanical (THM) | coupled problems in porous media | Wenqing Wang a,/C3, Georg Kosakowski b, Olaf Kolditz a,c | a Helmholtz Center for Environmental Research - UFZ, Leipzig, Germany | b Paul Scherrer Institut - PSI, Villigen, Switzerland | c Technical University of Dresden, Dresden, Germany | article info

### SOTA___OGS___Mont_Terri.zip

- Local copy: [SOTA___OGS___Mont_Terri.zip](../../source_files/SOTA___OGS___Mont_Terri.zip)
- Type: `zip`; size: 913451 bytes
- SHA1: `515611426288cc0c9430999f9906026e2da8b386`
- Original/raw provenance candidates: SOTA___OGS___Mont_Terri.zip
- ZIP members: 19; uncompressed bytes: 1153394
- ZIP extension counts: .bib=1; .pdf=1; .prj=1; .tex=2; .xml=14
- ZIP member CSV: [zip_member_deep_summary.csv](zip_member_deep_summary.csv)
- Keyword hits: OGS; niche
- First extracted lines / sheet headers: ogs_settings/01_processes_TRM.xml | ogs_settings/02_process_variables_TRM.xml | ogs_settings/03_parameters_TRM.xml | ogs_settings/04_1_media_aqu_liq.xml | ogs_settings/04_2_media_twophase.xml | ogs_settings/04_media_TRM.xml | ogs_settings/06_nonlinear_solver_T.xml | ogs_settings/07_linear_solver_T.xml | ogs_settings/08_08_open_niche_seasonal.xml | ogs_settings/08_curves.xml

### 01_processes_TRM.xml

- Local copy: [01_processes_TRM.xml](../../source_files/projection_example/01_processes_TRM.xml)
- Type: `text/data`; size: 1613 bytes
- SHA1: `848b5757431ad0d9323f74baf5845ca6c167cefa`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/01_processes_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/01_processes_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::01_processes_TRM.xml
- Searchable extract/outline: [01_processes_TRM_2a36437d.xml.head.txt](extracted_text/01_processes_TRM_2a36437d.xml.head.txt)
- Text/data line count: 34
- Keyword hits: saturation; pressure
- First extracted lines / sheet headers: <process> | <name>TRM</name> | <type>THERMO_RICHARDS_MECHANICS</type> | <integration_order>4</integration_order> | <!-- <dimension>2</dimension> --> | <!-- Gestein --> | <constitutive_relation id="0"> | <type>LinearElasticOrthotropic</type> | <youngs_moduli>E</youngs_moduli> | <shear_moduli>G</shear_moduli>

### 02_process_variables_TRM.xml

- Local copy: [02_process_variables_TRM.xml](../../source_files/projection_example/02_process_variables_TRM.xml)
- Type: `text/data`; size: 2378 bytes
- SHA1: `90e20c5ee5cf2f0ae1e9ee64458dbcb891ef5e13`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/02_process_variables_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/02_process_variables_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::02_process_variables_TRM.xml
- Searchable extract/outline: [02_process_variables_TRM_bd440385.xml.head.txt](extracted_text/02_process_variables_TRM_bd440385.xml.head.txt)
- Text/data line count: 73
- Keyword hits: pressure; CD-A; niche
- First extracted lines / sheet headers: <process_variable> | <name>displacement</name> | <components>2</components> | <order>2</order> | <initial_condition>ic_displacement</initial_condition> | <boundary_conditions> | <boundary_condition> | <mesh>cd-a_left</mesh> | <type>Dirichlet</type> | <component>0</component>

### 03_parameters_TRM.xml

- Local copy: [03_parameters_TRM.xml](../../source_files/projection_example/03_parameters_TRM.xml)
- Type: `text/data`; size: 5702 bytes
- SHA1: `fb5a72a1962119622da8c3d17837017bb2822749`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/03_parameters_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/03_parameters_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::03_parameters_TRM.xml
- Searchable extract/outline: [03_parameters_TRM_687d7167.xml.head.txt](extracted_text/03_parameters_TRM_687d7167.xml.head.txt)
- Text/data line count: 186
- Keyword hits: pressure; niche
- First extracted lines / sheet headers: <!-- IC --> | <parameter> | <name>ic_displacement</name> | <type>Constant</type> | <values>0 0</values> | <!--type>MeshNode</type> | <field_name>displacement</field_name--> | </parameter> | <parameter> | <name>ic_pressure</name> <!-- check pressure0 + ic_sigma0 -->

### 03_parameters_TRM_orig.xml

- Local copy: [03_parameters_TRM_orig.xml](../../source_files/projection_example/03_parameters_TRM_orig.xml)
- Type: `text/data`; size: 5601 bytes
- SHA1: `ff7c284ae234350b8d86e52cb788a00adb86cc70`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::03_parameters_TRM_orig.xml
- Searchable extract/outline: [03_parameters_TRM_orig_1c4eff7f.xml.head.txt](extracted_text/03_parameters_TRM_orig_1c4eff7f.xml.head.txt)
- Text/data line count: 183
- Keyword hits: pressure; niche
- First extracted lines / sheet headers: <!-- IC --> | <parameter> | <name>ic_displacement</name> | <type>Constant</type> | <values>0 0</values> | <!--type>MeshNode</type> | <field_name>displacement</field_name--> | </parameter> | <parameter> | <name>ic_pressure</name> <!-- check pressure0 + ic_sigma0 -->

### 04_1_media_aqu_liq.xml

- Local copy: [04_1_media_aqu_liq.xml](../../source_files/projection_example/04_1_media_aqu_liq.xml)
- Type: `text/data`; size: 2880 bytes
- SHA1: `8ba341270221506ef3b5deb94a3d7a9730515498`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_1_media_aqu_liq.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_1_media_aqu_liq.xml
- Searchable extract/outline: [04_1_media_aqu_liq_ddd3cfc6.xml.head.txt](extracted_text/04_1_media_aqu_liq_ddd3cfc6.xml.head.txt)
- Text/data line count: 78
- Keyword hits: ERT; pressure
- First extracted lines / sheet headers: <phase> | <type>AqueousLiquid</type> | <properties> | <property> | <name>specific_heat_capacity</name> | <type>Parameter</type> | <parameter_name>c_p_l</parameter_name> | </property> | <property> | <name>thermal_conductivity</name>

### 04_2_media_twophase.xml

- Local copy: [04_2_media_twophase.xml](../../source_files/projection_example/04_2_media_twophase.xml)
- Type: `text/data`; size: 792 bytes
- SHA1: `a57c40add0a8d37c39ba7c716063f7e6c5bc01a9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_2_media_twophase.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_2_media_twophase.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_2_media_twophase.xml
- Searchable extract/outline: [04_2_media_twophase_613df85e.xml.head.txt](extracted_text/04_2_media_twophase_613df85e.xml.head.txt)
- Text/data line count: 23
- Keyword hits: ERT; permeability; saturation
- First extracted lines / sheet headers: <property> | <name>relative_permeability</name> | <type>RelativePermeabilityVanGenuchten</type> | <residual_liquid_saturation>0.1</residual_liquid_saturation> | <residual_gas_saturation>0</residual_gas_saturation> | <exponent>0.45</exponent> | <minimum_relative_permeability_liquid>1e-25</minimum_relative_permeability_liquid> | </property> | <property> | <name>saturation</name>

### 04_media_TRM.xml

- Local copy: [04_media_TRM.xml](../../source_files/projection_example/04_media_TRM.xml)
- Type: `text/data`; size: 1950 bytes
- SHA1: `6b68ab641d97eeeadd965d73417ab4b645d4ffd2`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/04_media_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/04_media_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::04_media_TRM.xml
- Searchable extract/outline: [04_media_TRM_edd60c14.xml.head.txt](extracted_text/04_media_TRM_edd60c14.xml.head.txt)
- Text/data line count: 72
- Keyword hits: ERT; permeability; saturation; pressure; OGS
- First extracted lines / sheet headers: <!-- | Parameter, die in Ogs5 vorhanden waren, welche in Ogs6 bisher aber noch zu fehlen scheinen oder | nicht mehr benötigt werden: | PERMEABILITY_SATURATION | CAPILLARY_PRESSURE | STORAGE | --> | <medium id="0,1"><!--,2,3,4,6,7,8,9,11,12,13,14"--> | <properties> | <property>

### 05_1_fixed_timestepping.xml

- Local copy: [05_1_fixed_timestepping.xml](../../source_files/projection_example/05_1_fixed_timestepping.xml)
- Type: `text/data`; size: 2354 bytes
- SHA1: `6deeb611eee6d8d7f90c61de431ccaa579c4582a`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_1_fixed_timestepping.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_1_fixed_timestepping.xml
- Searchable extract/outline: [05_1_fixed_timestepping_1a4d4c6a.xml.head.txt](extracted_text/05_1_fixed_timestepping_1a4d4c6a.xml.head.txt)
- Text/data line count: 44
- First extracted lines / sheet headers: <time_stepping> | <type>FixedTimeStepping</type> | <t_initial>0</t_initial><!-- last time step --> | <t_end>140000000</t_end><!-- last time step of the curve --> | <!--t_initial>3153624278400</t_initial--><!-- last time step --> | <!--t_end>3153759099264</t_end--><!-- last time step of the curve --> | <timesteps> | <pair> | <repeat>365</repeat> | <delta_t>864000</delta_t><!--t0 = 18.09.2019; deltat= 10d so that first output is exported at the end of the month -->

### 05_time_loop_TRM.xml

- Local copy: [05_time_loop_TRM.xml](../../source_files/projection_example/05_time_loop_TRM.xml)
- Type: `text/data`; size: 1913 bytes
- SHA1: `9aeebe19310aad9fc2d096a1439648efaa214240`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/05_time_loop_TRM.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/05_time_loop_TRM.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::05_time_loop_TRM.xml
- Searchable extract/outline: [05_time_loop_TRM_9329ebe7.xml.head.txt](extracted_text/05_time_loop_TRM_9329ebe7.xml.head.txt)
- Text/data line count: 49
- Keyword hits: ERT; saturation; pressure; CD-A
- First extracted lines / sheet headers: <processes> | <process ref="TRM"> | <nonlinear_solver>basic_newton</nonlinear_solver> | <!--compensate_non_equilibrium_initial_residuum>true | </compensate_non_equilibrium_initial_residuum--> | <convergence_criterion> | <type>PerComponentDeltaX</type> | <norm_type>NORM2</norm_type> | <abstols>1e-10 1e-10 1e-10 1e-10</abstols> | <reltols>1e-8 1e-8 1e-8 1e-8</reltols>

### 06_nonlinear_solver_T.xml

- Local copy: [06_nonlinear_solver_T.xml](../../source_files/projection_example/06_nonlinear_solver_T.xml)
- Type: `text/data`; size: 185 bytes
- SHA1: `4ba846b864d87d955f03c67a79aafd4c94a410e1`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/06_nonlinear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::06_nonlinear_solver_T.xml
- Searchable extract/outline: [06_nonlinear_solver_T_430a9e88.xml.head.txt](extracted_text/06_nonlinear_solver_T_430a9e88.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <nonlinear_solver> | <name>basic_newton</name> | <type>Newton</type> | <max_iter>150</max_iter> | <linear_solver>general_linear_solver</linear_solver> | </nonlinear_solver>

### 07_linear_solver_T.xml

- Local copy: [07_linear_solver_T.xml](../../source_files/projection_example/07_linear_solver_T.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `56d3a8bb2867a99d0027597ef4e76e3e769b67d5`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/07_linear_solver_T.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/07_linear_solver_T.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::07_linear_solver_T.xml
- Searchable extract/outline: [07_linear_solver_T_5d9bfc5b.xml.head.txt](extracted_text/07_linear_solver_T_5d9bfc5b.xml.head.txt)
- Text/data line count: 6
- First extracted lines / sheet headers: <linear_solver> | <name>general_linear_solver</name> | <eigen> | <solver_type>PardisoLU</solver_type> | </eigen> | </linear_solver>

### 08_08_open_niche_seasonal.xml

- Local copy: [08_08_open_niche_seasonal.xml](../../source_files/projection_example/08_08_open_niche_seasonal.xml)
- Type: `text/data`; size: 35319 bytes
- SHA1: `235d07fa789046e0875b00e11583561a5d3a7910`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_08_open_niche_seasonal.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_08_open_niche_seasonal.xml
- Searchable extract/outline: [08_08_open_niche_seasonal_3b0832a4.xml.head.txt](extracted_text/08_08_open_niche_seasonal_3b0832a4.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>0.0 159740.3603603579 319480.72072071955 479221.0810810812 638961.4414414391 798701.8018018007 958442.1621621624 1118182.5225225203 1277922.882882882 1437663.2432432398 1597403.6036036015 1757143.963963963 1916884.324324321 2076624.6846846826 2236365.0450450443 2396105.405405402 2555845.765765764 2715586.1261261255 2875326.4864864834 3035066.846846845 3194807.2072072066 3354547.5675675645 3514287.927927926 3674028.288288288 3833768.6486486457 3993509.0090090074 4153249.369369369 4312989.729729727 4472730.090090089 4632470.45045045 4792210.810810808 4951951.17117117 5111691.531531531 5271431.891891889 5431172.252252251 5590912.612612613 5750652.97297297 5910393.333333332 6070133.693693694 6229874.054054052 6389614.414414413 6549354.774774775 6709095.135135133 6868835.495495494 7028575.855855852 7188316.216216214 7348056.576576576 7507796.93...

### 08_curves.xml

- Local copy: [08_curves.xml](../../source_files/projection_example/08_curves.xml)
- Type: `text/data`; size: 223 bytes
- SHA1: `d39fe15825540b8e805cbf6a81e953c62a9eeab9`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/08_curves.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/08_curves.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::08_curves.xml
- Searchable extract/outline: [08_curves_6fa7924a.xml.head.txt](extracted_text/08_curves_6fa7924a.xml.head.txt)
- Text/data line count: 10
- Keyword hits: niche
- First extracted lines / sheet headers: <curve> | <include file="./08_08_open_niche_seasonal.xml" /> <!--open_niche_seasonal_curve_shifted.xml" /--> | </curve> | <!-- | <curve> | <include file="./closed_niche_seasonal_curve_shifted.xml" /> | </curve> | -->

### README.txt

- Local copy: [README.txt](../../source_files/projection_example/README.txt)
- Type: `text/data`; size: 290 bytes
- SHA1: `56bad31bd49ace73b960a789eee550042f5cf5cf`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::README.txt
- Searchable extract/outline: [README_12a0e5b9.txt.head.txt](extracted_text/README_12a0e5b9.txt.head.txt)
- Text/data line count: 9
- Keyword hits: OGS
- First extracted lines / sheet headers: important changes: | *prj: mesh call | 03_param*: Function (projection) specification | domain identification bulk_all.vtu needs to be re-done with bulk.vtu | /home/ogs_auto_jenkins/release_versions/native/master/ogs6_v6.5.4/bin/identifySubdomains -m bulk_w_projections.vtu bulk_all.vtu

### bulk.vtu

- Local copy: [bulk.vtu](../../source_files/projection_example/bulk.vtu)
- Type: `vtu`; size: 1380973 bytes
- SHA1: `9a15c579914caab9012638f36af674ba7566a886`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::bulk.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/bulk.vtu

### bulk_all.vtu

- Local copy: [bulk_all.vtu](../../source_files/projection_example/bulk_all.vtu)
- Type: `vtu`; size: 1834288 bytes
- SHA1: `d77258e31b0c11e1d06e603d301c2767ce126241`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::bulk_all.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/bulk_all.vtu

### bulk_w_projections.vtu

- Local copy: [bulk_w_projections.vtu](../../source_files/projection_example/bulk_w_projections.vtu)
- Type: `vtu`; size: 828267 bytes
- SHA1: `4212e492e60fa84db7e282af558c814d1339f4eb`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::bulk_w_projections.vtu

### cd-a_bottom.vtu

- Local copy: [cd-a_bottom.vtu](../../source_files/projection_example/cd-a_bottom.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `53cd9e66076feb90da8cea5dde6f402ec85d0677`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_bottom.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_bottom.vtu

### cd-a_left.vtu

- Local copy: [cd-a_left.vtu](../../source_files/projection_example/cd-a_left.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `b6806808e3d17d91d571329e5466841cb64ed1ae`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_left.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_left.vtu

### cd-a_niche4.vtu

- Local copy: [cd-a_niche4.vtu](../../source_files/projection_example/cd-a_niche4.vtu)
- Type: `vtu`; size: 45643 bytes
- SHA1: `a27fa6ec2498321ee861b2e11891da96159b6d9d`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_niche4.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_niche4.vtu

### cd-a_right.vtu

- Local copy: [cd-a_right.vtu](../../source_files/projection_example/cd-a_right.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `678a306075bc04384fc7c935b5f137d2725bf171`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_right.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_right.vtu

### cd-a_top.vtu

- Local copy: [cd-a_top.vtu](../../source_files/projection_example/cd-a_top.vtu)
- Type: `vtu`; size: 4383 bytes
- SHA1: `3aecdaa221e9e78b748ad6b2abb734ecf8b1a7df`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd-a_top.vtu; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd-a_top.vtu

### cd_a_open_niche_quad.prj

- Local copy: [cd_a_open_niche_quad.prj](../../source_files/projection_example/cd_a_open_niche_quad.prj)
- Type: `text/data`; size: 1122 bytes
- SHA1: `185b473154b7079c4ce06225f9c793d2d8179b88`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/cd_a_open_niche_quad.prj; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::cd_a_open_niche_quad.prj; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/cd_a_open_niche_quad.prj
- Searchable extract/outline: [cd_a_open_niche_quad_05469784.prj.head.txt](extracted_text/cd_a_open_niche_quad_05469784.prj.head.txt)
- Text/data line count: 39
- Keyword hits: CD-A; niche
- First extracted lines / sheet headers: <?xml version="1.0" encoding="ISO-8859-1"?> | <OpenGeoSysProject> | <meshes> | <!--mesh>bulk.vtu</mesh--> | <mesh>bulk_w_projections.vtu</mesh> | <mesh>bulk_all.vtu</mesh> | <mesh>cd-a_niche4.vtu</mesh> | <mesh>cd-a_left.vtu</mesh> | <mesh>cd-a_right.vtu</mesh> | <mesh>cd-a_top.vtu</mesh>

### closed_niche_seasonal_curve_shifted.xml

- Local copy: [closed_niche_seasonal_curve_shifted.xml](../../source_files/projection_example/closed_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 146 bytes
- SHA1: `f126b5892d086319af536f698e293a0306da2075`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/closed_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::closed_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [closed_niche_seasonal_curve_shifted_816b759a.xml.head.txt](extracted_text/closed_niche_seasonal_curve_shifted_816b759a.xml.head.txt)
- Text/data line count: 3
- Keyword hits: niche
- First extracted lines / sheet headers: <name>closed_niche_seasonal_curve</name> | <coords>3153624278400.0 3153764278400.0</coords> | <values>116080.57942975157 116080.57942975157</values>

### comparison.pvsm

- Local copy: [comparison.pvsm](../../source_files/projection_example/comparison.pvsm)
- Type: `pvsm`; size: 793281 bytes
- SHA1: `1bf120a58cbbeb651dc9e24480fdf887bf7974de`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::comparison.pvsm

### generate_projections.py

- Local copy: [generate_projections.py](../../source_files/projection_example/generate_projections.py)
- Type: `py`; size: 1990 bytes
- SHA1: `141d6cce25fd8768278c8f70a8f8b40e0a2c45e3`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::generate_projections.py

### open_niche_seasonal_curve_shifted.xml

- Local copy: [open_niche_seasonal_curve_shifted.xml](../../source_files/projection_example/open_niche_seasonal_curve_shifted.xml)
- Type: `text/data`; size: 33881 bytes
- SHA1: `a306b331492c6da66796b4875f68f1b92f5c0af3`
- Original/raw provenance candidates: archive member SOTA___OGS___Mont_Terri.zip::ogs_settings/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-04-04_2d_model_container/CDA_N4_2D_250403.zip::CDA_N4_2D_250403/open_niche_seasonal_curve_shifted.xml; archive member cda_knowledge_base/file_transfers/collected/2025-05-09_updated_model/CDA_N4_2D_250509.zip::open_niche_seasonal_curve_shifted.xml
- Searchable extract/outline: [open_niche_seasonal_curve_shifted_043f08cd.xml.head.txt](extracted_text/open_niche_seasonal_curve_shifted_043f08cd.xml.head.txt)
- Text/data line count: 5
- Keyword hits: niche
- First extracted lines / sheet headers: <name>open_niche_seasonal_curve</name> | <coords>3153624278400.0 3153624438140.3604 3153624597880.7207 3153624757621.081 3153624917361.4414 3153625077101.802 3153625236842.162 3153625396582.5225 3153625556322.883 3153625716063.243 3153625875803.6035 3153626035543.964 3153626195284.324 3153626355024.6846 3153626514765.045 3153626674505.4053 3153626834245.7656 3153626993986.126 3153627153726.4863 3153627313466.8467 3153627473207.207 3153627632947.5674 3153627792687.9277 3153627952428.288 3153628112168.6484 3153628271909.009 3153628431649.369 3153628591389.7295 3153628751130.0903 3153628910870.4507 3153629070610.811 3153629230351.1714 3153629390091.5317 3153629549831.892 3153629709572.2524 3153629869312.613 3153630029052.973 3153630188793.3335 3153630348533.694 3153630508274.054 3153630668014.4146 3153630827754.775 3153630987495.1353 3153631147235.4956 3153631306975.856 3153631466716.2163 3...

### specifications.pptx

- Local copy: [specifications.pptx](../../source_files/projection_example/specifications.pptx)
- Type: `pptx`; size: 184636 bytes
- SHA1: `311225d341832515d360268ff97bb7126a66d5b4`
- Original/raw provenance candidates: archive member cda_knowledge_base/attachments/thunderbird_recovered/2025-09-05_Niche_4_no_gravity_no_sigV_no_uy_deltat_projection_on_mesh.zip::specifications.pptx
- Searchable extract/outline: [specifications_2ca482df.pptx.txt](extracted_text/specifications_2ca482df.pptx.txt)
- PPTX slides: 3; extracted text characters: 475
- First extracted lines / sheet headers: --- Slide 1 --- | ts_0000: 18.09.2019 | ts_0001: 18.09.2019 + 10 | days | => End | of | September 2019 | ts_0003: ts_001 + 1 | month | => End
