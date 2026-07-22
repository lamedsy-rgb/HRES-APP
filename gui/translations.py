# -*- coding: utf-8 -*-

TRANSLATIONS = {
    "fr": {
        "title": "Système d'Optimisation de Micro-Réseau Rural (HRES)",
        "sidebar_logo": "HRES App",
        "sidebar_subtitle": "Optimisation de Micro-Réseau",
        "theme_lbl": "Mode d'affichage:",
        "lang_lbl": "Langue / Language:",
        "session_lbl": "Gestion de Session :",
        "save_session": "Sauvegarder Session",
        "load_session": "Charger Session",
        
        # Tabs
        "tab_inputs": "Données",
        "tab_opt": "Optimisation",
        "tab_results": "Résultats",
        "tab_scenarios": "Comparatif",
        
        # Tab 1: Inputs
        "tab1_title": "Configuration & Données d'Entrée",
        "seg_manual": "Saisie Manuelle",
        "seg_file": "Importer Fichier",
        "seg_geoloc": "Géolocalisation",
        "community_title": "Paramètres de la Communauté",
        "preset_lbl": "Profil Communautaire Prédéfini :",
        "preset_custom": "Personnalisé",
        "preset_hamlet": "Hameau Isolé (15 foyers)",
        "preset_village": "Village Moyen (60 foyers)",
        "preset_center": "Grand Centre (250 foyers)",
        "households_lbl": "Ménages (Foyers)",
        "school_lbl": "Capacité de l'École:",
        "clinic_lbl": "Capacité du Centre de Santé:",
        "financial_title": "Paramètres Financiers ($ USD)",
        "pv_capex": "Solaire PV ($/kW)",
        "wind_capex": "Éolien ($/kW)",
        "bat_capex": "Batterie ($/kWh)",
        "diesel_capex": "Diesel ($/kW)",
        "fuel_price": "Carburant ($/L)",
        "apply_config": "APPLIQUER LA CONFIGURATION",
        "generating": "GÉNÉRATION EN COURS...",
        "status_synthetic_ready": "Profil de charge synthétique prêt à l'emploi (Démarrage)",
        "status_synthetic_updated": "Profils manuels régénérés avec succès !",
        
        # Tab 1: File Ingestion
        "weather_file_title": "1. Fichier Météo (Solaire, Vent, Température)",
        "load_file_title": "2. Fichier de Charge Électrique",
        "import_btn": "IMPORTER LE FICHIER...",
        "import_none": "Aucun fichier chargé (Profil synthétique actif)",
        "format_guide_title": "Guide de Formatage CSV/Excel :",
        "format_guide_desc": (
            "• Le fichier doit contenir 8760 lignes (une année complète).\n"
            "• Fichier Météo : Doit avoir les colonnes 'solar_irradiance', 'wind_speed', 'temperature'.\n"
            "• Fichier de Charge : Doit avoir la colonne 'total_load' ou 'load'."
        ),
        
        # Tab 1: Geolocation
        "geoloc_title": "Téléchargement NASA POWER (Météo)",
        "lat_lbl": "Latitude (-90 à 90) :",
        "lon_lbl": "Longitude (-180 à 180) :",
        "year_lbl": "Année Météo historique :",
        "nasa_btn": "INTERROGER L'API NASA POWER & METTRE À JOUR",
        "nasa_status_wait": "En attente de saisie. En cas d'absence de réseau, un profil physique réaliste sera généré.",
        "nasa_status_downloading": "TÉLÉCHARGEMENT DEPUIS LA NASA...",
        "nasa_status_fetching": "Appel de l'API en arrière-plan... Veuillez patienter.",
        "nasa_status_success": "Données chargées pour ({lat:.2f}°, {lon:.2f}°) !",
        
        # Previs optionmenu
        "previs_load": "Aperçu de la Charge",
        "previs_solar": "Aperçu de l'Irradiance",
        "previs_wind": "Aperçu du Vent",
        "previs_load_title": "Aperçu de la Charge Hebdomadaire (7 jours)",
        "previs_solar_title": "Moyenne Mensuelle de l'Irradiance Solaire",
        "previs_wind_title": "Vitesse Moyenne Mensuelle du Vent",
        "hours_of_week": "Heure de la semaine",
        "power_kw": "Puissance (kW)",
        "month": "Mois",
        
        # Tab 2: Optimization
        "tab2_title": "Contrôle de Sizing & Optimisation Algorithmique",
        "comp_selection_title": "Composants à inclure dans le Micro-Réseau :",
        "design_criteria": "Critères de Conception",
        "lolp_max": "Tolérance de coupure max (LOLP %)",
        "ga_params": "Paramètres de l'Algorithme Génétique",
        "generations": "Nombre de Générations",
        "pop_size": "Taille de Population",
        "force_numpy": "Forcer l'optimiseur NumPy natif (Sans PyGAD)",
        "run_opt": "LANCER L'OPTIMISATION DU MICRO-RÉSEAU",
        "opt_running": "OPTIMISATION EN COURS...",
        "opt_calculating": "Calcul des générations...",
        "opt_status_idle": "Statut: En attente de lancement",
        "opt_console_title": "Console d'Exécution & Diagnostic Algorithmique (Temps Réel)",
        
        # Tab 3: Results
        "tab3_title": "Résultats du Dimensionnement & Visualisation Temporelle",
        "optimal_capacity": "Puissances Optimales",
        "kpi_pv": "Solaire (PV)",
        "kpi_wind": "Éolien",
        "kpi_bat": "Batteries",
        "kpi_diesel": "Générateur Diesel",
        "perf_finance": "Performance & Éléments Financiers",
        "kpi_lcoe": "LCOE ($/kWh)",
        "kpi_npc": "NPC (Coût Net)",
        "kpi_fuel": "Carburant Annuel",
        "kpi_lolp": "LOLP (Taux de Coupure)",
        "kpi_ren": "Fraction Renouvelable",
        "kpi_soh": "SOH Batterie (1 an)",
        "curve_pv": "Solaire PV",
        "curve_wind": "Éolien",
        "curve_diesel": "Diesel",
        "curve_load": "Charge",
        "curve_soc": "SOC Batterie",
        "chart_hourly_title": "Dynamique de Production & Demande Horaire",
        "chart_hourly_y": "Puissance (kW)",
        "chart_hourly_x": "Date & Heure",
        "chart_share_title": "Répartition de la Production d'Énergie Annuelle (MWh)",
        
        # Tab 4: Scenario Comparison
        "tab4_title": "Comparateur et Gestionnaire de Scénarios Électriques",
        "scenario_actions": "Actions Scénario",
        "scenario_name": "Nom du scén. :",
        "btn_save_scenario": "SAUVEGARDER LE SCÉNARIO",
        "btn_reset_scenario": "RÉINITIALISER TOUT",
        "scenarios_saved_title": "Scénarios Sauvegardés",
        "scenario_info_text": (
            "Comparez les compromis :\n\n"
            "• L'optimalité varie selon les coûts unitaires et les profils.\n"
            "• Sauvegardez plusieurs architectures (ex: 'Solaire Pur', 'Hybride', 'Diesel Base') "
            "pour analyser l'impact du LCOE et de la fiabilité (LOLP)."
        ),
        
        # Message boxes & Dialogs
        "save_session_title": "Sauvegarder Session HRES",
        "load_session_title": "Ouvrir Session HRES",
        "success": "Succès",
        "error": "Erreur",
        "session_saved_msg": "La session a été sauvegardée avec succès !",
        "session_loaded_msg": "La session a été chargée avec succès !",
        "session_save_error": "Impossible de sauvegarder la session.",
        "session_load_error": "Impossible de charger la session.",
        "missing_data_error": "Veuillez charger des données météo et de charge avant d'optimiser.",
        "invalid_config_error": "Vous devez activer au moins un système de production (PV, Éolien ou Diesel).",
        "invalid_lat_lon": "Valeurs de géolocalisation invalides.",
        "select_excel_csv": "Sélectionner un fichier Excel ou CSV",
        "empty_scenario_name": "Veuillez entrer un nom de scénario valide.",
        
        # Other OptionMenu values
        "none": "Aucune",
        "small": "Petit",
        "medium": "Moyen",
        "large": "Grand",
        "exclu": "Exclu",
        
        # Tab 5: Help & Doc
        "tab_help": "Aide & Doc",
        "tab5_title": "Centre de Documentation & Aide Technique",
        "restart_tutorial_btn": "RELANCER LE DIDACTICIEL",
        "doc_project_context_title": "1. Contexte du Projet & Énergie Propre",
        "doc_project_context_text": "Ce système d'optimisation HRES (Hybrid Renewable Energy System) vise à dimensionner de manière optimale les micro-réseaux ruraux autonomes. En combinant l'énergie solaire, éolienne, le stockage par batterie et un générateur diesel d'appoint, il garantit un approvisionnement électrique stable au coût le plus bas possible (LCOE) tout en réduisant l'empreinte carbone pour les communautés isolées.",
        "doc_terms_title": "2. Définition des Termes Techniques",
        "doc_terms_text": "• LOLP (Loss of Load Probability) % : Probabilité de perte de charge. Indique la fraction de l'année (en %) durant laquelle la demande électrique n'est pas satisfaite par le système.\n• LCOE (Levelized Cost of Energy) : Coût actualisé de l'énergie ($/kWh). Calcule le coût moyen de génération d'un kWh sur la durée de vie du projet.\n• NPC (Net Present Cost) : Coût Net Actuel ($). Représente la somme actualisée de tous les coûts (investissement, remplacement, carburant, maintenance) moins les valeurs de récupération.\n• SOH (State of Health) : État de santé de la batterie (%). Indique le niveau de dégradation de la capacité de stockage après un an de simulation temporelle horaire.",
        "doc_models_title": "3. Modélisation Physique & Équations du Système",
        "doc_models_text": "• Solaire PV :\n  - Température de cellule : T_cell = T_amb + (G / 0.8) * (NOCT - 20)\n  - Puissance générée : P_PV = P_crête * f_déclassement * G * [1 + alpha_P * (T_cell - 25)]\n  (où G est l'irradiance solaire en kW/m² et alpha_P = -0.004 /°C est le coefficient de température de puissance)\n\n• Éolien :\n  - Correction de hauteur (vitesse au moyeu) : V_moyeu = V_anémomètre * (H_moyeu / H_anémomètre) ^ alpha (avec alpha = 0.14)\n  - Courbe de puissance cubique par morceaux :\n    * Si V < V_démarrage ou V >= V_coupure : P_éolienne = 0\n    * Si V_démarrage <= V < V_nominale : P_éolienne = P_nominale * [(V - V_démarrage) / (V_nominale - V_démarrage)]³\n    * Si V_nominale <= V < V_coupure : P_éolienne = P_nominale\n\n• Stockage par Batterie (BESS) :\n  - Charge (surplus) : E_bat(t) = E_bat(t-1) * (1 - self_décharge) + P_charge * delta_t * eff_charge\n  - Décharge (déficit) : E_bat(t) = E_bat(t-1) * (1 - self_décharge) - (P_décharge * delta_t) / eff_décharge\n  - Dégradation SOH : Cumul d'un vieillissement calendaire constant et d'une usure cyclique proportionnelle au débit d'énergie total cumulé traversant la batterie.\n\n• Groupe Diesel d'appoint :\n  - Consommation horaire : Fuel (L/h) = F0 * P_nominale + F1 * P_générée\n  - Charge minimale : P_générée >= 30% * P_nominale. Si la puissance requise est inférieure, le groupe fonctionne à 30% et le surplus charge la batterie.",
        "doc_ga_title": "4. Fonctionnement de l'Algorithme Génétique",
        "doc_ga_text": "L'optimiseur utilise un algorithme génétique pour explorer l'espace tridimensionnel des capacités (PV, Éolien, Batterie, Diesel). La taille de la population détermine le nombre de configurations testées en parallèle à chaque étape, tandis que le nombre de générations fixe le nombre d'itérations d'amélioration par sélection, croisement et mutation. Une population ou un nombre de générations plus élevé augmente la précision de la recherche globale mais allonge le temps de calcul.\n\n• Option \"Forcer l'optimiseur NumPy natif (Sans PyGAD)\" : L'application intègre deux moteurs d'optimisation : la bibliothèque externe PyGAD et un moteur alternatif personnalisé développé uniquement avec NumPy. Activer cette option force l'utilisation du moteur NumPy local. Cela garantit une stabilité et une compatibilité de calcul à 100% sur toutes les machines sans dépendre de modules ou compilateurs externes, tout en fournissant des résultats technico-économiques extrêmement similaires.",
        "doc_community_title": "5. Paramètres de la Communauté & Profils de Charge",
        "doc_community_text": "Les paramètres de la communauté définissent la demande électrique horaire synthétique sur 8760 heures :\n• Nombre de Ménages : Établit la charge de base résidentielle. Chaque foyer consomme de l'énergie pour l'éclairage et les appareils ménagers avec deux pics caractéristiques : le matin (6h-8h) et le soir (18h-22h).\n• École : Introduit une charge purement diurne active uniquement de 8h à 16h et du lundi au vendredi (nulle la nuit et le week-end). Elle favorise le dimensionnement solaire PV direct (autoconsommation immédiate sans batteries).\n• Centre de Santé (Clinique) : Crée une charge continue 24h/24 et 7j/7 pour assurer la conservation réfrigérée des vaccins/médicaments et l'éclairage nocturne. Elle augmente fortement le besoin en stockage par batterie pour couvrir la nuit.",
        
        # Tutorial Steps
        "tut_title": "Didacticiel Interactif HRES",
        "tut_next": "Suivant",
        "tut_prev": "Précédent",
        "tut_exit": "Quitter",
        "tut_finish": "Terminer",
        "tut_welcome_msg": "Bienvenue dans le didacticiel interactif HRES ! Ce guide va vous présenter les principales fonctionnalités de l'application en quelques étapes simples.",
        
        "tut_step0_title": "Bienvenue sur HRES App",
        "tut_step0_desc": "Optimisez et concevez des micro-réseaux hybrides renouvelables pour les communautés rurales. Laissez-vous guider à travers l'interface !",
        "tut_step1_title": "Saisie des Données d'Entrée",
        "tut_step1_desc": "Ajustez les paramètres de la communauté (foyers, école, dispensaire) et les coûts des équipements. Cliquez ensuite sur le bouton 'APPLIQUER LA CONFIGURATION' ci-dessous pour valider et mettre à jour la courbe de charge !",
        "tut_step2_title": "Géolocalisation & Cartographie",
        "tut_step2_desc": "Double-cliquez sur la carte ou saisissez les coordonnées géographiques, puis cliquez sur le bouton bleu ci-dessous pour télécharger automatiquement les données météo réelles de la NASA.",
        "tut_step3_title": "Paramètres d'Optimisation",
        "tut_step3_desc": "Définissez le LOLP % (la tolérance de coupure maximale autorisée de l'alimentation électrique, par exemple 5% signifie que le système accepte de ne pas couvrir la demande au maximum 5% des heures de l'année) et réglez les paramètres de l'algorithme génétique (générations et population).",
        "tut_step4_title": "Lancement de la Simulation",
        "tut_step4_desc": "Cliquez sur ce bouton vert pour lancer la simulation temporelle et l'optimisation génétique en temps réel. La console ci-dessous affichera le diagnostic.",
        "tut_step5_title": "Visualisation des Résultats",
        "tut_step5_desc": "Une fois optimisé, observez les capacités optimales recommandées, le coût NPC, le LCOE, ainsi que les graphiques interactifs de charge et de production horaire.",
        "tut_step6_title": "Comparaison de Scénarios",
        "tut_step6_desc": "Enregistrez vos configurations pour comparer différents scénarios (ex: solaire pur vs hybride diesel) sur le plan financier et technique.",
        
        # First launch dialog
        "first_launch_title": "Premier démarrage",
        "first_launch_question": "Souhaitez-vous lancer le didacticiel interactif pour découvrir l'application ?",
    },
    
    "en": {
        "title": "Rural Microgrid Optimization System (HRES)",
        "sidebar_logo": "HRES App",
        "sidebar_subtitle": "Microgrid Optimization",
        "theme_lbl": "Appearance Mode:",
        "lang_lbl": "Language / Langue:",
        "session_lbl": "Session Management:",
        "save_session": "Save Session",
        "load_session": "Load Session",
        
        # Tabs
        "tab_inputs": "Inputs",
        "tab_opt": "Optimization",
        "tab_results": "Results",
        "tab_scenarios": "Scenarios",
        
        # Tab 1: Inputs
        "tab1_title": "Configuration & Input Data",
        "seg_manual": "Manual Input",
        "seg_file": "Import File",
        "seg_geoloc": "Geolocation",
        "community_title": "Community Parameters",
        "preset_lbl": "Preset Community Profile:",
        "preset_custom": "Custom",
        "preset_hamlet": "Isolated Hamlet (15 households)",
        "preset_village": "Average Village (60 households)",
        "preset_center": "Large Center (250 households)",
        "households_lbl": "Households",
        "school_lbl": "School Capacity:",
        "clinic_lbl": "Health Clinic Capacity:",
        "financial_title": "Financial Parameters ($ USD)",
        "pv_capex": "Solar PV ($/kW)",
        "wind_capex": "Wind ($/kW)",
        "bat_capex": "Battery ($/kWh)",
        "diesel_capex": "Diesel ($/kW)",
        "fuel_price": "Fuel ($/L)",
        "apply_config": "APPLY CONFIGURATION",
        "generating": "GENERATING...",
        "status_synthetic_ready": "Synthetic load profile ready for use (Startup)",
        "status_synthetic_updated": "Manual profiles successfully regenerated!",
        
        # Tab 1: File Ingestion
        "weather_file_title": "1. Weather File (Solar, Wind, Temperature)",
        "load_file_title": "2. Electric Load Profile File",
        "import_btn": "IMPORT FILE...",
        "import_none": "No file loaded (Synthetic profile active)",
        "format_guide_title": "CSV/Excel Formatting Guide:",
        "format_guide_desc": (
            "• The file must contain exactly 8760 rows (a full year).\n"
            "• Weather File: Must have columns named 'solar_irradiance', 'wind_speed', 'temperature'.\n"
            "• Load File: Must have a column named 'total_load' or 'load'."
        ),
        
        # Tab 1: Geolocation
        "geoloc_title": "Download NASA POWER (Weather)",
        "lat_lbl": "Latitude (-90 to 90):",
        "lon_lbl": "Longitude (-180 to 180):",
        "year_lbl": "Historical Weather Year:",
        "nasa_btn": "QUERY NASA POWER API & UPDATE",
        "nasa_status_wait": "Awaiting input. If offline, a realistic physical default profile will be generated.",
        "nasa_status_downloading": "DOWNLOADING FROM NASA...",
        "nasa_status_fetching": "Calling API in background... Please wait.",
        "nasa_status_success": "Data loaded for ({lat:.2f}°, {lon:.2f}°)!",
        
        # Previs optionmenu
        "previs_load": "Load Preview",
        "previs_solar": "Solar GHI Preview",
        "previs_wind": "Wind Speed Preview",
        "previs_load_title": "Weekly Load Profile Preview (7 Days)",
        "previs_solar_title": "Monthly Average Solar Irradiance",
        "previs_wind_title": "Monthly Average Wind Speed",
        "hours_of_week": "Hour of the week",
        "power_kw": "Power (kW)",
        "month": "Month",
        
        # Tab 2: Optimization
        "tab2_title": "Sizing Control & Algorithmic Optimization",
        "comp_selection_title": "Microgrid components to include:",
        "design_criteria": "Design Constraints",
        "lolp_max": "Max Loss of Load (LOLP %)",
        "ga_params": "Genetic Algorithm Parameters",
        "generations": "Number of Generations",
        "pop_size": "Population Size",
        "force_numpy": "Force native NumPy optimizer (Without PyGAD)",
        "run_opt": "RUN MICROGRID OPTIMIZATION",
        "opt_running": "OPTIMIZATION IN PROGRESS...",
        "opt_calculating": "Calculating generations...",
        "opt_status_idle": "Status: Awaiting start",
        "opt_console_title": "Execution Console & Algorithmic Diagnostics (Real-time)",
        
        # Tab 3: Results
        "tab3_title": "Optimal Sizing Results & Hourly Dynamics",
        "optimal_capacity": "Optimal Capacities",
        "kpi_pv": "Solar (PV)",
        "kpi_wind": "Wind",
        "kpi_bat": "Batteries",
        "kpi_diesel": "Diesel Generator",
        "perf_finance": "Performance & Financials",
        "kpi_lcoe": "LCOE ($/kWh)",
        "kpi_npc": "NPC (Net Cost)",
        "kpi_fuel": "Annual Fuel",
        "kpi_lolp": "LOLP (Outage Rate)",
        "kpi_ren": "Renewable Fraction",
        "kpi_soh": "Battery SOH (1 Year)",
        "curve_pv": "Solar PV",
        "curve_wind": "Wind",
        "curve_diesel": "Diesel",
        "curve_load": "Load",
        "curve_soc": "Battery SOC",
        "chart_hourly_title": "Hourly Generation & Demand Dynamics",
        "chart_hourly_y": "Power (kW)",
        "chart_hourly_x": "Date & Hour",
        "chart_share_title": "Annual Generation Share breakdown (MWh)",
        
        # Tab 4: Scenario Comparison
        "tab4_title": "Electrical Scenario Manager & Comparator",
        "scenario_actions": "Scenario Actions",
        "scenario_name": "Scenario Name:",
        "btn_save_scenario": "SAVE SCENARIO",
        "btn_reset_scenario": "RESET ALL",
        "scenarios_saved_title": "Saved Scenarios",
        "scenario_info_text": (
            "Compare tradeoffs:\n\n"
            "• Optimality changes based on unit costs and resource profiles.\n"
            "• Save multiple configurations (e.g., 'Solar Only', 'Hybrid', 'Base Diesel') "
            "to analyze LCOE vs reliability (LOLP) impacts."
        ),
        
        # Message boxes & Dialogs
        "save_session_title": "Save HRES Session",
        "load_session_title": "Open HRES Session",
        "success": "Success",
        "error": "Error",
        "session_saved_msg": "The session has been saved successfully!",
        "session_loaded_msg": "The session has been loaded successfully!",
        "session_save_error": "Failed to save the session.",
        "session_load_error": "Failed to load the session.",
        "missing_data_error": "Please load weather and load profiles before optimizing.",
        "invalid_config_error": "You must enable at least one generation system (PV, Wind, or Diesel).",
        "invalid_lat_lon": "Invalid latitude or longitude values.",
        "select_excel_csv": "Select Excel or CSV File",
        "empty_scenario_name": "Please enter a valid scenario name.",
        
        # Other OptionMenu values
        "none": "None",
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
        "exclu": "Excluded",
        
        # Tab 5: Help & Doc
        "tab_help": "Help & Doc",
        "tab5_title": "Documentation Center & Technical Help",
        "restart_tutorial_btn": "RESTART TUTORIAL",
        "doc_project_context_title": "1. Project Context & Clean Energy",
        "doc_project_context_text": "This HRES (Hybrid Renewable Energy System) optimization system is designed to optimally size autonomous rural microgrids. By combining solar power, wind power, battery storage, and a backup diesel generator, it guarantees a stable power supply at the lowest possible levelized cost (LCOE) while reducing the carbon footprint of isolated communities.",
        "doc_terms_title": "2. Technical Terms Definitions",
        "doc_terms_text": "• LOLP (Loss of Load Probability) % : Loss of load probability. Indicates the fraction of the year (in %) during which the electric demand is not met by the system.\n• LCOE (Levelized Cost of Energy) : The average cost of generating one kWh of electricity over the project lifespan ($/kWh).\n• NPC (Net Present Cost) : Net Present Cost ($). Represents the discounted sum of all costs (capital, replacement, fuel, O&M) minus salvage values.\n• SOH (State of Health) : Battery state of health (%). Indicates the capacity degradation of the battery storage after one year of hourly simulation.",
        "doc_models_title": "3. Physical Modeling & System Equations",
        "doc_models_text": "• Solar PV:\n  - Cell Temperature: T_cell = T_amb + (G / 0.8) * (NOCT - 20)\n  - Generated Power: P_PV = P_rated * f_derating * G * [1 + alpha_P * (T_cell - 25)]\n  (where G is solar irradiance in kW/m² and alpha_P = -0.004 /°C is the power temperature coefficient)\n\n• Wind System:\n  - Hub Height Wind Speed Correction: V_hub = V_anemometer * (H_hub / H_anemometer) ^ alpha (with exponent alpha = 0.14)\n  - Piecewise Cubic Power Curve:\n    * If V < V_cut_in or V >= V_cut_out: P_wind = 0\n    * If V_cut_in <= V < V_rated: P_wind = P_rated * [(V - V_cut_in) / (V_rated - V_cut_in)]³\n    * If V_rated <= V < V_cut_out: P_wind = P_rated\n\n• Battery Storage (BESS):\n  - Charging (surplus): E_bat(t) = E_bat(t-1) * (1 - self_discharge) + P_charge * delta_t * eff_charge\n  - Discharging (deficit): E_bat(t) = E_bat(t-1) * (1 - self_discharge) - (P_discharge * delta_t) / eff_discharge\n  - SOH Degradation: Combines calendar aging and cyclic degradation based on cumulative energy throughput.\n\n• Backup Diesel Generator:\n  - Hourly Fuel Consumption: Fuel (L/hr) = F0 * P_rated + F1 * P_generated\n  - Min Load Constraint: P_generated >= 30% * P_rated. If load falls below 30%, the generator runs at 30% min capacity and excess generation is used to charge batteries.",
        "doc_ga_title": "4. Genetic Algorithm Principles",
        "doc_ga_text": "The optimizer uses a genetic algorithm to search the 3D space of system capacities (PV, Wind, Battery, Diesel). The population size determines how many configurations are tested in parallel, and the number of generations sets the iterations of selection, crossover, and mutation. Higher population or generations increase global search accuracy but require longer computational time.\n\n• Option \"Force native NumPy optimizer (Without PyGAD)\": The application integrates two optimization engines: the external PyGAD library and a custom alternative engine built entirely on NumPy. Checking this option forces the use of the native NumPy engine. This ensures 100% stability and compatibility across all platforms without depending on third-party compiled modules, while delivering very similar performance.",
        "doc_community_title": "5. Community Parameters & Load Profiles Impact",
        "doc_community_text": "The community inputs define the synthetic hourly electricity demand over 8760 hours:\n• Number of Households: Scales the residential baseline load. Each household consumes power for lighting and basic appliances with two distinct peaks: morning (6:00-8:00) and evening (18:00-22:00).\n• School: Introduces a purely daytime load active only from 8:00 to 16:00, Monday to Friday. Zero load during nights and weekends. Midday peaks favor direct solar PV sizing.\n• Health Clinic: Creates a constant 24/7 load for vaccine storage refrigeration and night lighting. It heavily increases battery storage capacity needs to cover the night load.",
        
        # Tutorial Steps
        "tut_title": "HRES Interactive Tutorial",
        "tut_next": "Next",
        "tut_prev": "Back",
        "tut_exit": "Exit",
        "tut_finish": "Finish",
        "tut_welcome_msg": "Welcome to the HRES interactive tutorial! This guide will walk you through the main features of the app in a few simple steps.",
        
        "tut_step0_title": "Welcome to HRES App",
        "tut_step0_desc": "Optimize and design hybrid renewable microgrids for rural communities. Let's explore the interface together!",
        "tut_step1_title": "Input Data Panel",
        "tut_step1_desc": "Adjust community parameters (households, school, health clinic) and component costs. Then click the 'APPLY CONFIGURATION' button below to validate and update the load profile!",
        "tut_step2_title": "Map & Geolocation",
        "tut_step2_desc": "Double-click on the map or input geographic coordinates, then click the blue button below to automatically download real meteorological data using NASA POWER API.",
        "tut_step3_title": "Optimization Constraints",
        "tut_step3_desc": "Set the LOLP % (the maximum allowed power outage tolerance, e.g. 5% means the system accepts not serving the load for at most 5% of the hours of the year) and configure Genetic Algorithm parameters.",
        "tut_step4_title": "Run Simulation",
        "tut_step4_desc": "Click this green button to run the hourly simulation and genetic optimization. The execution console below will output real-time diagnostics.",
        "tut_step5_title": "Results and KPI Visualization",
        "tut_step5_desc": "Review the optimal sizing outputs, NPC, LCOE, and interactive hourly production charts once the optimization completes.",
        "tut_step6_title": "Scenario Comparison",
        "tut_step6_desc": "Save different run configurations (e.g. solar-only vs diesel base) to compare their financial costs and technical reliability.",
        
        # First launch dialog
        "first_launch_title": "First Launch",
        "first_launch_question": "Would you like to run the interactive tutorial to discover the application?",
    },
    
    "ar": {
        "title": "نظام تحسين الشبكة الصغيرة الريفية (HRES)",
        "sidebar_logo": "تطبيق HRES",
        "sidebar_subtitle": "تحسين الشبكة الصغيرة الريفية",
        "theme_lbl": "مظهر العرض:",
        "lang_lbl": "اللغة / Language:",
        "session_lbl": "إدارة الجلسة:",
        "save_session": "حفظ الجلسة",
        "load_session": "تحميل الجلسة",
        
        # Tabs
        "tab_inputs": "المدخلات",
        "tab_opt": "التحسين",
        "tab_results": "النتائج",
        "tab_scenarios": "المقارنة",
        
        # Tab 1: Inputs
        "tab1_title": "التهيئة وبيانات المدخلات",
        "seg_manual": "إدخال يدوي",
        "seg_file": "استيراد ملف",
        "seg_geoloc": "الموقع الجغرافي",
        "community_title": "معطيات المجتمع المحلي",
        "preset_lbl": "ملف تعريف المجتمع الجاهز:",
        "preset_custom": "مخصص",
        "preset_hamlet": "قرية معزولة (15 منزلًا)",
        "preset_village": "قرية متوسطة (60 منزلًا)",
        "preset_center": "مركز كبير (250 منزلًا)",
        "households_lbl": "عدد المنازل (العائلات)",
        "school_lbl": "سعة المدرسة:",
        "clinic_lbl": "سعة المركز الصحي:",
        "financial_title": "المعايير المالية ($ بالدولار)",
        "pv_capex": "شمسي كهروضوئي ($/كيلوواط)",
        "wind_capex": "طاقة الرياح ($/كيلوواط)",
        "bat_capex": "البطارية ($/كيلوواط ساعة)",
        "diesel_capex": "الديزل ($/كيلوواط)",
        "fuel_price": "سعر الوقود ($/لتر)",
        "apply_config": "تطبيق الإعدادات",
        "generating": "جاري التوليد...",
        "status_synthetic_ready": "ملف تعريف الحمل الاصطناعي جاهز للاستخدام (البدء)",
        "status_synthetic_updated": "تمت إعادة توليد ملفات التعريف اليدوية بنجاح!",
        
        # Tab 1: File Ingestion
        "weather_file_title": "1. ملف الطقس (الإشعاع الشمسي، الرياح، الحرارة)",
        "load_file_title": "2. ملف نمط الحمل الكهربائي",
        "import_btn": "استيراد الملف...",
        "import_none": "لم يتم تحميل أي ملف (الملف الاصطناعي نشط)",
        "format_guide_title": "دليل تنسيق ملف CSV/Excel:",
        "format_guide_desc": (
            "• يجب أن يحتوي الملف على 8760 صفًا بالضبط (سنة كاملة).\n"
            "• ملف الطقس: يجب أن يحتوي على أعمدة باسم 'solar_irradiance'، 'wind_speed'، 'temperature'.\n"
            "• ملف الحمل: يجب أن يحتوي على عمود باسم 'total_load' أو 'load'."
        ),
        
        # Tab 1: Geolocation
        "geoloc_title": "تحميل من NASA POWER (الطقس)",
        "lat_lbl": "خط العرض (-90 إلى 90):",
        "lon_lbl": "خط الطول (-180 إلى 180):",
        "year_lbl": "سنة الطقس التاريخية:",
        "nasa_btn": "الاستعلام عن واجهة NASA POWER وتحديثها",
        "nasa_status_wait": "في انتظار المدخلات. في حالة عدم وجود شبكة، سيتم توليد ملف طقس افتراضي واقعي.",
        "nasa_status_downloading": "جاري التحميل من وكالة ناسا...",
        "nasa_status_fetching": "الاتصال بواجهة برمجة التطبيقات في الخلفية... يرجى الانتظار.",
        "nasa_status_success": "تم تحميل البيانات للموقع ({lat:.2f}°، {lon:.2f}°)!",
        
        # Previs optionmenu
        "previs_load": "معاينة الحمل",
        "previs_solar": "معاينة الإشعاع الشمسي",
        "previs_wind": "معاينة سرعة الرياح",
        "previs_load_title": "معاينة نمط الحمل الأسبوعي (7 أيام)",
        "previs_solar_title": "المعدل الشهري للإشعاع الشمسي",
        "previs_wind_title": "المعدل الشهري لسرعة الرياح",
        "hours_of_week": "ساعات الأسبوع",
        "power_kw": "القدرة (كيلوواط)",
        "month": "الشهر",
        
        # Tab 2: Optimization
        "tab2_title": "التحكم في تحديد الأحجام والتحسين الخوارزمي",
        "comp_selection_title": "المكونات المراد تضمينها في الشبكة الصغيرة :",
        "design_criteria": "معايير التصميم والقيود",
        "lolp_max": "أقصى احتمال لفقدان الحمل (LOLP %)",
        "ga_params": "معطيات الخوارزمية الجينية (GA)",
        "generations": "عدد الأجيال",
        "pop_size": "حجم المجتمع",
        "force_numpy": "إجبار المحسن NumPy المحلي (بدون مكتبة PyGAD)",
        "run_opt": "بدء تحسين الشبكة الصغيرة",
        "opt_running": "جاري التحسين...",
        "opt_calculating": "جاري حساب الأجيال المتعاقبة...",
        "opt_status_idle": "الحالة: في انتظار البدء",
        "opt_console_title": "لوحة تشغيل الخوارزمية والتشخيص (الوقت الفعلي)",
        
        # Tab 3: Results
        "tab3_title": "نتائج تحديد الأحجام المثلى وحركة التشغيل التفصيلية",
        "optimal_capacity": "الأحجام والقدرات المثلى",
        "kpi_pv": "الطاقة الشمسية (PV)",
        "kpi_wind": "طاقة الرياح",
        "kpi_bat": "البطاريات",
        "kpi_diesel": "مولد الديزل",
        "perf_finance": "الأداء المالي والتشغيلي",
        "kpi_lcoe": "تكلفة الطاقة المستوية (LCOE)",
        "kpi_npc": "التكلفة الصافية الإجمالية (NPC)",
        "kpi_fuel": "الوقود السنوي المستهلك",
        "kpi_lolp": "احتمال انقطاع التيار (LOLP)",
        "kpi_ren": "حصة الطاقة المتجددة",
        "kpi_soh": "سلامة البطارية SOH (سنة واحدة)",
        "curve_pv": "شمسي كهروضوئي",
        "curve_wind": "رياح",
        "curve_diesel": "الديزل",
        "curve_load": "الحمل",
        "curve_soc": "حالة شحن البطارية",
        "chart_hourly_title": "ديناميكية الإنتاج والطلب الساعي على مدار الوقت",
        "chart_hourly_y": "القدرة (كيلوواط)",
        "chart_hourly_x": "التاريخ والوقت",
        "chart_share_title": "توزيع إنتاج الطاقة السنوي الإجمالي (ميجاواط ساعة)",
        
        # Tab 4: Scenario Comparison
        "tab4_title": "مقارن ومدير سيناريوهات الشبكة الكهربائية",
        "scenario_actions": "خيارات السيناريو",
        "scenario_name": "اسم السيناريو:",
        "btn_save_scenario": "حفظ السيناريو الحالي",
        "btn_reset_scenario": "إعادة تعيين الكل",
        "scenarios_saved_title": "السيناريوهات المحفوظة للمقارنة",
        "scenario_info_text": (
            "مقارنة المقايضات الاقتصادية والتقنية :\n\n"
            "• تتغير الأحجام المثلى بتغير التكاليف الأحادية وملفات الطقس.\n"
            "• احفظ سيناريوهات متعددة (مثل: 'شمسي فقط'، 'ديزل فقط'، 'هجين') "
            "لمقارنة تكلفة الكيلوواط الساعي LCOE مقابل الموثوقية LOLP."
        ),
        
        # Message boxes & Dialogs
        "save_session_title": "حفظ جلسة HRES الحالية",
        "load_session_title": "فتح جلسة HRES مسجلة",
        "success": "تم بنجاح",
        "error": "خطأ",
        "session_saved_msg": "تم حفظ الجلسة بنجاح !",
        "session_loaded_msg": "تم تحميل الجلسة واستعادتها بنجاح !",
        "session_save_error": "فشل حفظ ملف الجلسة.",
        "session_load_error": "فشل تحميل واستعادة ملف الجلسة.",
        "missing_data_error": "يرجى استيراد أو توليد بيانات الطقس والأحمال قبل البدء بالتحسين.",
        "invalid_config_error": "يجب تفعيل مصدر إنتاج طاقة واحد على الأقل (شمس، رياح، أو ديزل).",
        "invalid_lat_lon": "قيم الإحداثيات الجغرافية غير صالحة.",
        "select_excel_csv": "اختر ملف Excel أو CSV لنمط الحمل",
        "empty_scenario_name": "يرجى كتابة اسم سيناريو صحيح ومقبول.",
        
        # Other OptionMenu values
        "none": "لا يوجد",
        "small": "صغير",
        "medium": "متوسط",
        "large": "كبير",
        "exclu": "مستبعد",
        
        # Tab 5: Help & Doc
        "tab_help": "المساعدة والتوثيق",
        "tab5_title": "مركز التوثيق والدعم الفني",
        "restart_tutorial_btn": "إعادة تشغيل الدليل التعليمي",
        "doc_project_context_title": "1. سياق المشروع والطاقة النظيفة",
        "doc_project_context_text": "تم تصميم نظام تحسين HRES (نظام الطاقة المتجددة الهجين) لتحديد الأحجام المثلى للشبكات الكهربائية الريفية الصغيرة المستقلة. من خلال الجمع بين الطاقة الشمسية وطاقة الرياح وتخزين البطاريات ومولد الديزل الاحتياطي، يضمن النظام إمدادًا مستقرًا بالطاقة بأقل تكلفة ممكنة للكيلوواط ساعة (LCOE) مع تقليل البصمة الكربونية للمجتمعات المعزولة.",
        "doc_terms_title": "2. تعريف المصطلحات الفنية",
        "doc_terms_text": "• LOLP (احتمال فقدان الحمل) % : يشير إلى نسبة ساعات السنة (كنسبة مئوية) التي لا يلبي فيها النظام الطلب على الكهرباء.\n• LCOE (تكلفة الطاقة المستوية) : متوسط تكلفة توليد كيلوواط ساعة واحد من الكهرباء على مدار عمر المشروع ($/كيلوواط ساعة).\n• NPC (التكلفة الصافية الإجمالية) : التكلفة الصافية الإجمالية ($). تمثل مجموع التكاليف المخصومة (رأس المال، الاستبدال، الوقود، التشغيل والصيانة) مطروحًا منها القيمة المتبقية.\n• SOH (حالة الصحة للبطارية) : حالة صحة البطارية (%). توضح مدى تراجع سعة تخزين البطارية بعد عام كامل من المحاكاة الساعية.",
        "doc_models_title": "3. النمذجة الفيزيائية والمعادلات المستخدمة",
        "doc_models_text": "• الخلايا الكهروضوئية شمسية:\n  - درجة حرارة الخلية: T_cell = T_amb + (G / 0.8) * (NOCT - 20)\n  - الطاقة الناتجة: P_PV = P_rated * f_derating * G * [1 + alpha_P * (T_cell - 25)]\n  (حيث G هو الإشعاع الشمسي بكيلوواط/م² و alpha_P = -0.004 /°C هو معامل درجة الحرارة للقدرة)\n\n• طاقة الرياح:\n  - تصحيح سرعة الرياح حسب ارتفاع المحور: V_hub = V_anemometer * (H_hub / H_anemometer) ^ alpha (مع الأس alpha = 0.14)\n  - منحنى القدرة التكعيبي المجزأ:\n    * إذا كانت V < V_cut_in أو V >= V_cut_out: فإن P_wind = 0\n    * إذا كانت V_cut_in <= V < V_rated: فإن P_wind = P_rated * [(V - V_cut_in) / (V_rated - V_cut_in)]³\n    * إذا كانت V_rated <= V < V_cut_out: فإن P_wind = P_rated\n\n• نظام تخزين البطارية:\n  - الشحن (الفائض): E_bat(t) = E_bat(t-1) * (1 - self_discharge) + P_charge * delta_t * eff_charge\n  - التفريغ (العجز): E_bat(t) = E_bat(t-1) * (1 - self_discharge) - (P_discharge * delta_t) / eff_discharge\n  - تدهور البطارية SOH: يجمع بين التقادم الزمني والتآكل الدوري الناتج عن كمية الطاقة التراكمية الممررة.\n\n• مولد الديزل الاحتياطي:\n  - معدل استهلاك الوقود الساعي: Fuel (L/hr) = F0 * P_rated + F1 * P_generated\n  - قيد الحد الأدنى للحمل: P_generated >= 30% * P_rated. إذا كان الحمل المطلوب أقل، يعمل المولد بنسبة 30% ويشحن الفائض البطاريات.",
        "doc_ga_title": "4. مبادئ الخوارزمية الجينية",
        "doc_ga_text": "يستخدم المحسن خوارزمية جينية للبحث في الفضاء ثلاثي الأبعاد لسعة النظام (شمسي، رياح، بطارية، ديزل). يحدد حجم المجتمع عدد التهيئات التي يتم اختبارها بالتوازي، ويحدد عدد الأجيال عدد التكرارات للتحسين من خلال الانتخاب والعبور والطفرات. يؤدي زيادة حجم المجتمع أو عدد الأجيال إلى زيادة دقة البحث ولكنه يتطلب وقتًا أطول للحساب.\n\n• خيار \"إجبار المحسن NumPy المحلي (بدون مكتبة PyGAD)\": يدمج التطبيق محركين للتحسين: مكتبة PyGAD الخارجية ومحرك محلي مخصص تم تطويره بالكامل باستخدام NumPy. يؤدي تفعيل هذا الخيار إلى إجبار التطبيق على استخدام محرك NumPy المحلي. يضمن ذلك استقرارًا وتوافقًا بنسبة 100% على جميع الأجهزة دون الاعتماد على مكتبات خارجية، مع تقديم أداء وسرعة مماثلين للغاية.",
        "doc_community_title": "5. تأثير معطيات المجتمع ومواصفات الحمل",
        "doc_community_text": "تحدد مدخلات المجتمع منحنى الطلب الساعي على الكهرباء طوال 8760 ساعة:\n• عدد المنازل: يحدد خط الأساس السكني للحمل. يستهلك كل منزل الطاقة للإضاءة والأجهزة مع ذروتين: صباحية (6:00-8:00) ومسائية (18:00-22:00).\n• المدرسة: تضيف حملاً نهارياً فقط من 8:00 إلى 16:00، من الاثنين إلى الجمعة (صفر ليلاً وفي عطلة نهاية الأسبوع). هذا الحمل النهاري يشجع على زيادة سعة الألواح الشمسية المباشرة (الاستهلاك الفوري دون بطاريات).\n• العيادة الصحية: تضيف حملاً ثابتاً على مدار الساعة (24/7) لتشغيل مبردات الأدوية واللقاحات والإضاءة الليلية. يزيد هذا الحمل بشكل كبير من الحاجة لتخزين البطاريات لتغطية الليل.",
        
        # Tutorial Steps
        "tut_title": "الدليل التعليمي التفاعلي لـ HRES",
        "tut_next": "التالي",
        "tut_prev": "السابق",
        "tut_exit": "خروج",
        "tut_finish": "إنهاء",
        "tut_welcome_msg": "مرحبًا بك في الدليل التعليمي التفاعلي لـ HRES! سيقوم هذا الدليل بإرشادك عبر الميزات الرئيسية للتطبيق في خطوات بسيطة.",
        
        "tut_step0_title": "مرحبًا بك في تطبيق HRES",
        "tut_step0_desc": "قم بتصميم وتحسين شبكات صغيرة هجينة متجددة للمجتمعات الريفية. دعنا نستكشف الواجهة معًا!",
        "tut_step1_title": "لوحة بيانات المدخلات",
        "tut_step1_desc": "قم بتعديل معايير المجتمع (المنازل، المدرسة، المركز الصحي) وتكاليف المعدات. ثم انقر على زر 'تطبيق التهيئة' أدناه لاعتماد وتحديث منحنى الحمل!",
        "tut_step2_title": "الخريطة والموقع الجغرافي",
        "tut_step2_desc": "انقر مزدوجًا على الخريطة أو أدخل الإحداثيات الجغرافية، ثم انقر على الزر الأزرق أدناه لتحميل بيانات الطقس الفعلية تلقائيًا من ناسا.",
        "tut_step3_title": "قيود ومعايير التحسين",
        "tut_step3_desc": "قم بتعيين قيمة LOLP % (الحد الأقصى المسموح به لانقطاع التيار الكهربائي، على سبيل المثال 5% تعني قبول عدم تلبية الطلب لمدة لا تتجاوز 5% من ساعات السنة) واضبط معطيات الخوارزمية الجينية.",
        "tut_step4_title": "تشغيل المحاكاة",
        "tut_step4_desc": "انقر فوق هذا الزر الأخضر لبدء المحاكاة الساعية والتحسين الجيني. ستعرض لوحة التشغيل أدناه رسائل التشخيص في الوقت الفعلي.",
        "tut_step5_title": "عرض النتائج والمؤشرات",
        "tut_step5_desc": "راجع مخرجات الأحجام المثلى، وتكلفة NPC، وتكلفة الطاقة LCOE، والرسوم البيانية التفاعلية للإنتاج الساعي والطلب بمجرد اكتمال العملية.",
        "tut_step6_title": "مقارنة السيناريوهات",
        "tut_step6_desc": "احفظ تهيئات التشغيل المختلفة (مثل الطاقة الشمسية فقط مقابل الديزل الأساسي) لمقارنة تكلفتها المالية وموثوقيتها التقنية.",
        
        # First launch dialog
        "first_launch_title": "التشغيل الأول",
        "first_launch_question": "هل ترغب في تشغيل الدليل التعليمي التفاعلي لاستكشاف التطبيق؟",
    }
}
