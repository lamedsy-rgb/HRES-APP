/* ==========================================================================
   HRES Optimizer v2.0 — Executive Single-Page Application Logic
   Features:
     - FR / EN / AR (RTL) Live Localization
     - Dark / Light Theme Persistence & Dynamic Chart/Map Styling
     - Leaflet Map (CartoDB Dark Matter, CartoDB Voyager, Esri Satellite)
     - 7-Day & Monthly Preview Charts + Custom CSV/Excel Weather Upload
     - Async GA Optimization with Live Progress Bar & Convergence Chart
     - Instant Manual What-If 8,760h Simulator
     - Interactive Week 1-52 Dispatch & Battery SOC Explorer
     - 1-Click Bankable A4 HTML/PDF Report Export
     - Multi-Scenario Comparator + 3-Benchmark Generator + CSV Export
     - 100% Graceful Offline Fallback when Leaflet/Chart.js CDN unavailable
   ========================================================================== */

(() => {
  "use strict";

  // ------------------------------------------------------------------------
  // 1. Translations Dictionary (FR / EN / AR)
  // ------------------------------------------------------------------------
  const I18N = {
    fr: {
      brand_sub: "Dimensionnement Technico-Économique de Micro-Réseaux (8 760 h)",
      tab_data: "Données & Carte",
      tab_optimize: "Optimisation",
      tab_results: "Résultats & Graphiques",
      tab_compare: "Comparatif",
      tab_docs: "Aide & Doc",
      card_site_title: "Site & Données Météorologiques",
      card_site_sub: "Cliquez sur la carte ou choisissez une ville de référence",
      quick_cities: "Villes de référence",
      lbl_site_name: "Nom du site / Projet",
      lbl_lat: "Latitude (°N)",
      lbl_lon: "Longitude (°E)",
      lbl_year: "Année Météo",
      lbl_weather_src: "Source Météo (8 760 h)",
      src_synthetic: "Synthétique Offline (Instantané)",
      src_nasa: "NASA POWER API (Cache + Live)",
      btn_fetch_weather: "Charger / Actualiser les Données Météo",
      upload_title: "Importer un fichier météo personnalisé (CSV / Excel)",
      upload_sub: "Colonnes requises : solar_irradiance, temperature, wind_speed (8 760 lignes)",
      card_load_title: "Profil de Demande Communautaire",
      card_load_sub: "Synthèse horaire résidentielle, scolaire et clinique 24/7",
      community_presets: "Préréglages Communautaires",
      preset_hamlet: "Hameau (15)",
      preset_village: "Village (60)",
      preset_center: "Centre (250)",
      lbl_households: "Ménages (Foyers)",
      lbl_school: "École",
      lbl_clinic: "Clinique / Centre Santé",
      opt_none: "Aucune",
      opt_small: "Petite",
      opt_medium: "Moyenne",
      opt_large: "Grande",
      card_fin_title: "Paramètres Financiers & Coûts ($ USD)",
      toggle_expand: "CAPEX / Carburant / Actualisation",
      lbl_pv_capex: "CAPEX PV ($/kWp)",
      lbl_wind_capex: "CAPEX Éolien ($/kW)",
      lbl_bat_capex: "CAPEX Batterie ($/kWh)",
      lbl_diesel_capex: "CAPEX Diesel ($/kW)",
      lbl_fuel_price: "Prix Carburant ($/L)",
      lbl_discount: "Taux d'Actualisation (%)",
      lbl_lifetime: "Durée du Projet (ans)",
      btn_reset_costs: "Réinitialiser",
      card_map_title: "Carte Interactive & Ressources du Site",
      stat_annual_load: "Demande Annuelle",
      stat_peak_load: "Pic de Charge",
      stat_ghi: "Irradiation GHI",
      stat_wind: "Vent Moyen (10m)",
      card_preview_title: "Prévisualisation des Profils",
      card_preview_sub: "Charge communautaire (7 jours) et potentiel solaire / éolien mensuel",
      prev_load: "Charge (7j)",
      prev_solar: "Solaire GHI",
      prev_wind: "Vent (m/s)",
      chart_offline_msg: "Mode hors-ligne : Chart.js indisponible. Les simulations, tableaux et rapports HTML/PDF restent 100 % fonctionnels.",
      btn_goto_opt: "Configurer l'Optimisation →",
      card_arch_opt_title: "Architecture & Bornes de Recherche",
      card_arch_opt_sub: "Activez les technologies à dimensionner par l'Algorithme Génétique",
      tech_pv: "Solaire Photovoltaïque (kWp)",
      tech_wind: "Éolien (kW)",
      tech_bat: "Stockage Batterie BESS (kWh)",
      tech_diesel: "Groupe Diesel d'Appoint (kW)",
      card_ga_params: "Paramètres de l'Algorithme Génétique",
      ga_mode_lbl: "Mode d'Exécution",
      mode_quick: "Démo Rapide (~1s)",
      mode_balanced: "Équilibré (~3s)",
      mode_precision: "Haute Précision (~8s)",
      lbl_gens: "Générations",
      lbl_pop: "Taille Population",
      lbl_lolp_max: "Contrainte Fiabilité — LOLP Max",
      btn_run_opt: "Lancer l'Optimisation GA (8 760 h)",
      card_live_opt: "Suivi & Convergence en Temps Réel",
      opt_ready_desc: "Prêt à rechercher la taille optimale minimisant le LCOE",
      lbl_progress: "Avancement",
      lbl_gen_curr: "Génération",
      lbl_best_lcoe: "Meilleur LCOE",
      lbl_elapsed: "Temps écoulé",
      lbl_console: "Journal d'Exécution",
      card_manual_title: "Simulation Manuelle Instantanée (What-If)",
      card_manual_sub: "Testez instantanément une architecture personnalisée sur 8 760 heures (< 50 ms)",
      btn_run_manual: "Simuler cette Configuration Instantanément",
      btn_save_scenario: "Enregistrer Scénario",
      btn_export_report: "Exporter Rapport Bancable (PDF/HTML)",
      kpi_lcoe: "LCOE (Coût Actualisé)",
      kpi_npc: "Coût Net Actuel (NPC)",
      kpi_capex: "Investissement (CAPEX)",
      kpi_rf: "Fraction Renouvelable",
      kpi_lolp: "Fiabilité / LOLP",
      kpi_fuel: "Carburant Diesel Annuel",
      kpi_co2: "CO₂ Évité par An",
      kpi_soh: "Santé Batterie (SOH An 1)",
      arch_pv: "Solaire PV",
      arch_wind: "Éolien",
      arch_bat: "Stockage Batterie (BESS)",
      arch_diesel: "Groupe Diesel",
      chart_dispatch_title: "Dispatch Horaire (168 h) & État de Charge Batterie (SOC)",
      chart_dispatch_sub: "Explorez n'importe quelle semaine de l'année (Semaine 1 à 52)",
      season_winter: "Hiver (S3)",
      season_spring: "Printemps (S15)",
      season_summer: "Été (S24)",
      season_autumn: "Automne (S42)",
      chart_monthly_title: "Production Mensuelle vs. Demande (MWh)",
      chart_monthly_sub: "Bilan énergétique agrégé sur 12 mois",
      chart_cost_title: "Décomposition du NPC & CAPEX ($)",
      chart_cost_sub: "Flux actualisés sur la durée de vie du projet",
      cost_view_npc: "NPC Cycle de Vie",
      cost_view_capex: "CAPEX Initial",
      mix_card_title: "Mix Énergétique",
      mix_card_sub: "Répartition annuelle & fraction renouvelable",
      mix_ring_label: "MIX ÉNERGÉTIQUE",
      mix_solar: "SOLAIRE PV",
      mix_bess: "BESS TRANSFÉRÉ",
      mix_wind: "ÉOLIEN",
      mix_diesel: "APPOINT DIESEL",
      tbl_energy_title: "Bilan Énergétique Annuel",
      tbl_fin_title: "Synthèse Financière Actualisée (NPC)",
      col_metric: "Indicateur",
      col_value: "Valeur",
      col_cost_item: "Poste Financier",
      col_usd: "Montant ($ USD)",
      cmp_title: "Comparatif Multi-Scénarios",
      cmp_sub: "Comparez vos architectures enregistrées (ex. 100 % Diesel vs. Solaire+BESS vs. Hybride)",
      btn_gen_benchmarks: "Générer 3 Scénarios de Référence",
      btn_export_csv: "Exporter CSV",
      btn_clear_all: "Tout Effacer",
      cmp_col_name: "Scénario",
      cmp_col_wind: "Éolien (kW)",
      cmp_col_bat: "BESS (kWh)",
      cmp_col_co2: "CO₂ Évité (t/an)",
      cmp_empty: "Aucun scénario enregistré. Enregistrez un résultat depuis l'onglet Résultats ou générez les 3 benchmarks automatiques.",
      cmp_chart_lcoe: "Comparaison LCOE ($/kWh) & Fraction Renouvelable (%)",
      cmp_chart_npc: "Comparaison NPC vs. CAPEX Initial (k$)",
      doc_header_title: "Modèles Physiques, Dispatch EMS & Équations Financières",
      doc_header_sub: "Toutes les simulations sont exécutées chronologiquement heure par heure (8 760 pas de temps par an).",
      doc_pv_title: "1. Modèle Solaire Photovoltaïque (PV)",
      doc_pv_desc: "Intègre la température de cellule (NOCT) et le coefficient de dégradation thermique des modules sous irradiance horaire G (kW/m²).",
      doc_wind_title: "2. Modèle Éolien (Loi de Cisaillement & Courbe Cubique)",
      doc_wind_desc: "Extrapole la vitesse du vent mesurée à 10 m vers la hauteur de moyeu (50 m), puis applique une courbe de puissance cubique par morceaux.",
      doc_bat_title: "3. Stockage Batterie (BESS) — SOC & Vieillissement SOH",
      doc_bat_desc: "Suit l'état de charge (20 %–100 %), les rendements de charge/décharge, les limites de taux C (0.5 C), l'autodécharge horaire et la perte de capacité cyclique.",
      doc_diesel_title: "4. Groupe Diesel d'Appoint & Règle de Charge Minimale",
      doc_diesel_desc: "Courbe linéaire de consommation de Willans avec plancher de charge à 30 % pour éviter le glaçage moteur ; tout surplus recharge la batterie.",
      doc_fin_title: "5. Analyse Financière (NPC, CRF, LCOE) & Fiabilité",
      doc_fin_desc: "Actualise l'ensemble des flux (investissement initial, maintenance fixe, carburant, remplacements périodiques et valeur résiduelle) sur la durée du projet.",
      doc_csv_title: "6. Format des Fichiers Météo Personnalisés (CSV / Excel)",
      doc_csv_desc: "Importez facilement vos propres mesures météorologiques (ou un export NASA POWER / PVGIS) depuis l'onglet Données & Carte :",
      doc_csv_note: "Les années bissextiles (8 784 lignes) et délimiteurs point-virgule (;) sont automatiquement normalisés.",
      months: ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"],
      week_label: "Semaine",
      best_tag: "MEILLEUR",
      toast_opt_done: "Optimisation GA terminée avec succès !",
      toast_sim_done: "Simulation 8 760 h terminée.",
      toast_saved: "Scénario enregistré dans le comparatif.",
      toast_report_ok: "Rapport bancable généré avec succès.",
      toast_upload_ok: "Fichier météo importé avec succès.",
      toast_bench_ok: "3 scénarios de référence générés.",
    },
    en: {
      brand_sub: "Rural Microgrid Techno-Economic Sizing Suite (8,760 h)",
      tab_data: "Data & Map",
      tab_optimize: "Optimization",
      tab_results: "Results & Charts",
      tab_compare: "Comparison",
      tab_docs: "Help & Docs",
      card_site_title: "Site & Meteorological Data",
      card_site_sub: "Click anywhere on the map or pick a benchmark city",
      quick_cities: "Reference Cities",
      lbl_site_name: "Site / Project Name",
      lbl_lat: "Latitude (°N)",
      lbl_lon: "Longitude (°E)",
      lbl_year: "Weather Year",
      lbl_weather_src: "Weather Source (8,760 h)",
      src_synthetic: "Offline Synthetic (Instant)",
      src_nasa: "NASA POWER API (Cached + Live)",
      btn_fetch_weather: "Load / Refresh Weather Data",
      upload_title: "Upload Custom Weather File (CSV / Excel)",
      upload_sub: "Required columns: solar_irradiance, temperature, wind_speed (8,760 rows)",
      card_load_title: "Community Load Profile Builder",
      card_load_sub: "Hourly residential, school, and 24/7 health clinic demand",
      community_presets: "Community Presets",
      preset_hamlet: "Hamlet (15)",
      preset_village: "Village (60)",
      preset_center: "Center (250)",
      lbl_households: "Households",
      lbl_school: "School",
      lbl_clinic: "Health Clinic",
      opt_none: "None",
      opt_small: "Small",
      opt_medium: "Medium",
      opt_large: "Large",
      card_fin_title: "Financial & Cost Assumptions ($ USD)",
      toggle_expand: "CAPEX / Fuel / Discount Rate",
      lbl_pv_capex: "PV CAPEX ($/kWp)",
      lbl_wind_capex: "Wind CAPEX ($/kW)",
      lbl_bat_capex: "Battery CAPEX ($/kWh)",
      lbl_diesel_capex: "Diesel CAPEX ($/kW)",
      lbl_fuel_price: "Diesel Fuel Price ($/L)",
      lbl_discount: "Discount Rate (%)",
      lbl_lifetime: "Project Lifetime (yrs)",
      btn_reset_costs: "Reset Defaults",
      card_map_title: "Interactive Site Map & Resource Summary",
      stat_annual_load: "Annual Demand",
      stat_peak_load: "Peak Load",
      stat_ghi: "Daily GHI",
      stat_wind: "Mean Wind (10m)",
      card_preview_title: "Resource & Demand Preview",
      card_preview_sub: "7-day community load profile and monthly solar / wind potential",
      prev_load: "Load (7d)",
      prev_solar: "Solar GHI",
      prev_wind: "Wind (m/s)",
      chart_offline_msg: "Offline mode: Chart.js CDN unreachable. Simulations, summary tables, and offline HTML/PDF reports remain 100% operational.",
      btn_goto_opt: "Configure Optimization →",
      card_arch_opt_title: "Architecture & Search Bounds",
      card_arch_opt_sub: "Enable technologies for Genetic Algorithm joint sizing",
      tech_pv: "Solar Photovoltaic (kWp)",
      tech_wind: "Wind Turbine (kW)",
      tech_bat: "Battery Storage BESS (kWh)",
      tech_diesel: "Backup Diesel Genset (kW)",
      card_ga_params: "Genetic Algorithm Parameters",
      ga_mode_lbl: "Optimization Preset",
      mode_quick: "Quick Demo (~1s)",
      mode_balanced: "Balanced (~3s)",
      mode_precision: "High Precision (~8s)",
      lbl_gens: "Generations",
      lbl_pop: "Population Size",
      lbl_lolp_max: "Reliability Target — Max LOLP",
      btn_run_opt: "Run GA Optimization (8,760 h)",
      card_live_opt: "Live Progress & Convergence",
      opt_ready_desc: "Ready to search optimal capacities minimizing LCOE",
      lbl_progress: "Progress",
      lbl_gen_curr: "Generation",
      lbl_best_lcoe: "Best LCOE",
      lbl_elapsed: "Elapsed",
      lbl_console: "Execution Log",
      card_manual_title: "Instant Manual Simulator (What-If)",
      card_manual_sub: "Evaluate any custom sizing across 8,760 hours instantly (< 50 ms)",
      btn_run_manual: "Simulate Custom Sizing Instantly",
      btn_save_scenario: "Save Scenario",
      btn_export_report: "Export Bankable Report (PDF/HTML)",
      kpi_lcoe: "LCOE (Levelized Cost)",
      kpi_npc: "Net Present Cost (NPC)",
      kpi_capex: "Initial CAPEX",
      kpi_rf: "Renewable Fraction",
      kpi_lolp: "Reliability / LOLP",
      kpi_fuel: "Annual Diesel Fuel",
      kpi_co2: "Annual CO₂ Avoided",
      kpi_soh: "Battery SOH (Year 1)",
      arch_pv: "Solar PV",
      arch_wind: "Wind Turbine",
      arch_bat: "Battery Storage (BESS)",
      arch_diesel: "Backup Diesel",
      chart_dispatch_title: "Hourly Dispatch (168 h) & Battery State of Charge (SOC)",
      chart_dispatch_sub: "Inspect any week of the year interactively (Week 1 to 52)",
      season_winter: "Winter (W3)",
      season_spring: "Spring (W15)",
      season_summer: "Summer (W24)",
      season_autumn: "Autumn (W42)",
      chart_monthly_title: "Monthly Energy Generation vs. Load (MWh)",
      chart_monthly_sub: "Aggregated 12-month simulation energy balance",
      chart_cost_title: "Lifecycle NPC & Initial CAPEX Breakdown ($)",
      chart_cost_sub: "Discounted cash flows over project lifetime",
      cost_view_npc: "Lifecycle NPC",
      cost_view_capex: "Initial CAPEX",
      mix_card_title: "Energy Mix",
      mix_card_sub: "Annual supply share & renewable fraction",
      mix_ring_label: "ENERGY MIX",
      mix_solar: "SOLAR PV",
      mix_bess: "BESS SHIFTED",
      mix_wind: "WIND TURBINE",
      mix_diesel: "DIESEL BACKUP",
      tbl_energy_title: "Annual Energy Balance",
      tbl_fin_title: "Discounted Cash-Flow Summary (NPC)",
      col_metric: "Metric",
      col_value: "Value",
      col_cost_item: "Financial Item",
      col_usd: "Amount ($ USD)",
      cmp_title: "Multi-Scenario Comparator",
      cmp_sub: "Compare saved architectures side-by-side (e.g. 100% Diesel vs. Solar+BESS vs. Hybrid)",
      btn_gen_benchmarks: "Generate 3 Benchmark Scenarios",
      btn_export_csv: "Export CSV",
      btn_clear_all: "Clear All",
      cmp_col_name: "Scenario",
      cmp_col_wind: "Wind (kW)",
      cmp_col_bat: "BESS (kWh)",
      cmp_col_co2: "CO₂ Avoided (t/yr)",
      cmp_empty: "No scenarios saved yet. Save a run from the Results tab or generate the 3 automatic benchmarks.",
      cmp_chart_lcoe: "LCOE ($/kWh) & Renewable Fraction (%) Comparison",
      cmp_chart_npc: "Net Present Cost vs. Initial CAPEX ($k)",
      doc_header_title: "Physics Models, EMS Dispatch & Financial Equations",
      doc_header_sub: "All simulations execute chronologically hour-by-hour (8,760 time steps per year).",
      doc_pv_title: "1. Solar Photovoltaic (PV) Model",
      doc_pv_desc: "Accounts for Nominal Operating Cell Temperature (NOCT) and thermal power derating under hourly irradiance G (kW/m²).",
      doc_wind_title: "2. Wind Turbine Model (Shear Power Law & Cubic Curve)",
      doc_wind_desc: "Extrapolates 10m anemometer wind speed to 50m hub height, then evaluates a piecewise cubic power curve.",
      doc_bat_title: "3. Battery Storage (BESS) — SOC & Cyclic SOH Aging",
      doc_bat_desc: "Tracks state of charge (20%–100%), charge/discharge efficiency, C-rate caps (0.5C), hourly self-discharge, and cyclic throughput degradation.",
      doc_diesel_title: "4. Backup Diesel Genset & 30% Minimum Load Rule",
      doc_diesel_desc: "Linear Willans fuel consumption curve with a 30% minimum load constraint to prevent engine wet-stacking; excess output charges the BESS.",
      doc_fin_title: "5. Financial Evaluation (NPC, CRF, LCOE) & Reliability",
      doc_fin_desc: "Discounts initial CAPEX, fixed O&M, fuel, periodic component replacements, and residual salvage value over the project lifetime.",
      doc_csv_title: "6. Custom Weather File Format (CSV / Excel)",
      doc_csv_desc: "Upload your own meteorological time series (or NASA POWER / PVGIS export) from the Data & Map tab:",
      doc_csv_note: "Leap-year files (8,784 rows), semicolon delimiters, and W/m² → kW/m² conversions are handled automatically.",
      months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
      week_label: "Week",
      best_tag: "BEST",
      toast_opt_done: "GA optimization completed successfully!",
      toast_sim_done: "8,760h simulation completed.",
      toast_saved: "Scenario saved to comparator.",
      toast_report_ok: "Bankable report generated successfully.",
      toast_upload_ok: "Custom weather file uploaded successfully.",
      toast_bench_ok: "3 benchmark scenarios generated.",
    },
    ar: {
      brand_sub: "منصة التصميم التقني والاقتصادي للشبكات الصغيرة الهجينة (8,760 ساعة)",
      tab_data: "البيانات والخريطة",
      tab_optimize: "التحسين",
      tab_results: "النتائج والرسوم",
      tab_compare: "المقارنة",
      tab_docs: "المساعدة والتوثيق",
      card_site_title: "الموقع وبيانات الطقس",
      card_site_sub: "انقر على الخريطة أو اختر مدينة مرجعية",
      quick_cities: "مدن مرجعية",
      lbl_site_name: "اسم الموقع / المشروع",
      lbl_lat: "خط العرض (°N)",
      lbl_lon: "خط الطول (°E)",
      lbl_year: "سنة الطقس",
      lbl_weather_src: "مصدر بيانات الطقس",
      src_synthetic: "اصطناعي محلي (فوري بدون إنترنت)",
      src_nasa: "NASA POWER API (مباشر + مخزن)",
      btn_fetch_weather: "تحميل / تحديث بيانات الطقس",
      upload_title: "رفع ملف طقس مخصص (CSV / Excel)",
      upload_sub: "الأعمدة المطلوبة: solar_irradiance, temperature, wind_speed (8,760 صف)",
      card_load_title: "منشئ منحنى الطلب المجتمعي",
      card_load_sub: "توليد ساعي للمنازل والمدرسة والعيادة الطبية على مدار 24/7",
      community_presets: "إعدادات مسبقة للمجتمع",
      preset_hamlet: "قرية صغيرة (15)",
      preset_village: "قرية متوسطة (60)",
      preset_center: "مركز كبير (250)",
      lbl_households: "عدد المنازل (العائلات)",
      lbl_school: "المدرسة",
      lbl_clinic: "العيادة / المركز الصحي",
      opt_none: "لا يوجد",
      opt_small: "صغيرة",
      opt_medium: "متوسطة",
      opt_large: "كبيرة",
      card_fin_title: "المعايير المالية والتكاليف ($ USD)",
      toggle_expand: "الاستثمار / الوقود / معدل الخصم",
      lbl_pv_capex: "تكلفة الشمسية ($/kWp)",
      lbl_wind_capex: "تكلفة الرياح ($/kW)",
      lbl_bat_capex: "تكلفة البطاريات ($/kWh)",
      lbl_diesel_capex: "تكلفة الديزل ($/kW)",
      lbl_fuel_price: "سعر الديزل ($/لتر)",
      lbl_discount: "معدل الخصم (%)",
      lbl_lifetime: "عمر المشروع (سنوات)",
      btn_reset_costs: "إعادة الضبط",
      card_map_title: "الخريطة التفاعلية وملخص الموارد",
      stat_annual_load: "الطلب السنوي",
      stat_peak_load: "ذروة الحمل",
      stat_ghi: "الإشعاع الشمسي",
      stat_wind: "متوسط الرياح (10م)",
      card_preview_title: "معاينة المنحنيات",
      card_preview_sub: "الطلب المجتمعي (7 أيام) والإمكانات الشمسية والرياحية الشهرية",
      prev_load: "الحمل (7 أيام)",
      prev_solar: "الإشعاع GHI",
      prev_wind: "الرياح (م/ث)",
      chart_offline_msg: "الوضع غير المتصل: مكتبة الرسوم غير متاحة. تظل المحاكاة والجداول والتقارير تعمل بنسبة 100%.",
      btn_goto_opt: "الانتقال إلى التحسين ←",
      card_arch_opt_title: "البنية وحدود البحث",
      card_arch_opt_sub: "اختر المكونات المراد تحجيمها بالخوارزمية الجينية",
      tech_pv: "الطاقة الشمسية (kWp)",
      tech_wind: "توربينات الرياح (kW)",
      tech_bat: "تخزين البطاريات BESS (kWh)",
      tech_diesel: "مولد الديزل الاحتياطي (kW)",
      card_ga_params: "معلمات الخوارزمية الجينية",
      ga_mode_lbl: "وضع التشغيل",
      mode_quick: "عرض سريع (~1ث)",
      mode_balanced: "متوازن (~3ث)",
      mode_precision: "دقة عالية (~8ث)",
      lbl_gens: "عدد الأجيال",
      lbl_pop: "حجم المجتمع",
      lbl_lolp_max: "حد الموثوقية — أقصى LOLP",
      btn_run_opt: "تشغيل التحسين بالخوارزمية الجينية",
      card_live_opt: "التقدم والتقارب المباشر",
      opt_ready_desc: "جاهز للبحث عن السعات المثلى لتقليل LCOE",
      lbl_progress: "التقدم",
      lbl_gen_curr: "الجيل",
      lbl_best_lcoe: "أفضل LCOE",
      lbl_elapsed: "الوقت المنقضي",
      lbl_console: "سجل التنفيذ",
      card_manual_title: "محاكاة يدوية فورية (What-If)",
      card_manual_sub: "اختبر أي تحجيم مخصص على 8,760 ساعة فوراً (< 50 مللي ثانية)",
      btn_run_manual: "محاكاة هذه البنية فوراً",
      btn_save_scenario: "حفظ السيناريو",
      btn_export_report: "تصدير التقرير الهندسي (PDF/HTML)",
      kpi_lcoe: "التكلفة المستوية (LCOE)",
      kpi_npc: "التكلفة الصافية (NPC)",
      kpi_capex: "الاستثمار الأولي (CAPEX)",
      kpi_rf: "نسبة الطاقة المتجددة",
      kpi_lolp: "الموثوقية / LOLP",
      kpi_fuel: "وقود الديزل السنوي",
      kpi_co2: "CO₂ المتجنب سنوياً",
      kpi_soh: "صحة البطارية (السنة 1)",
      arch_pv: "الطاقة الشمسية",
      arch_wind: "طاقة الرياح",
      arch_bat: "تخزين البطاريات",
      arch_diesel: "مولد الديزل",
      chart_dispatch_title: "التوزيع الساعي (168 ساعة) وحالة شحن البطارية (SOC)",
      chart_dispatch_sub: "استكشف أي أسبوع في السنة تفاعلياً (الأسبوع 1 إلى 52)",
      season_winter: "الشتاء (أ3)",
      season_spring: "الربيع (أ15)",
      season_summer: "الصيف (أ24)",
      season_autumn: "الخريف (أ42)",
      chart_monthly_title: "الإنتاج الشهري مقابل الطلب (MWh)",
      chart_monthly_sub: "الميزان الشهري للطاقة على مدار 12 شهراً",
      chart_cost_title: "تفصيل التكلفة الإجمالية NPC و CAPEX ($)",
      chart_cost_sub: "التدفقات النقدية المخصومة طوال عمر المشروع",
      cost_view_npc: "تفصيل NPC",
      cost_view_capex: "الاستثمار CAPEX",
      mix_card_title: "مزيج الطاقة",
      mix_card_sub: "التوزيع السنوي ونسبة الطاقة المتجددة",
      mix_ring_label: "مزيج الطاقة",
      mix_solar: "الطاقة الشمسية",
      mix_bess: "تخزين البطاريات",
      mix_wind: "طاقة الرياح",
      mix_diesel: "الديزل الاحتياطي",
      tbl_energy_title: "الميزان السنوي للطاقة",
      tbl_fin_title: "ملخص التكلفة الصافية المخصومة (NPC)",
      col_metric: "المؤشر",
      col_value: "القيمة",
      col_cost_item: "البند المالي",
      col_usd: "المبلغ ($ USD)",
      cmp_title: "مقارنة السيناريوهات المتعددة",
      cmp_sub: "قارن بين البنيات المحفوظة جنباً إلى جنب (ديزل 100% مقابل شمسي مقابل هجين)",
      btn_gen_benchmarks: "توليد 3 سيناريوهات مرجعية",
      btn_export_csv: "تصدير CSV",
      btn_clear_all: "مسح الكل",
      cmp_col_name: "السيناريو",
      cmp_col_wind: "رياح (kW)",
      cmp_col_bat: "بطارية (kWh)",
      cmp_col_co2: "CO₂ متجنب (طن/سنة)",
      cmp_empty: "لا توجد سيناريوهات محفوظة بعد. احفظ نتيجة من تبويب النتائج أو أنشئ 3 سيناريوهات مرجعية.",
      cmp_chart_lcoe: "مقارنة LCOE ($/kWh) ونسبة المتجددة (%)",
      cmp_chart_npc: "مقارنة NPC مقابل CAPEX الأولي ($k)",
      doc_header_title: "النماذج الفيزيائية والتوزيع EMS والمعادلات المالية",
      doc_header_sub: "تُنفذ جميع المحاكاة زمنياً ساعة بساعة (8,760 خطوة سنوياً).",
      doc_pv_title: "1. نموذج الطاقة الشمسية الكهروضوئية (PV)",
      doc_pv_desc: "يحسب درجة حرارة الخلية (NOCT) والتدهور الحراري للألواح تحت الإشعاع الساعي G.",
      doc_wind_title: "2. نموذج طاقة الرياح (قص الرياح والمنحنى التكعيبي)",
      doc_wind_desc: "يصحح سرعة الرياح من ارتفاع 10م إلى ارتفاع المحور 50م ويطبق منحنى قدرة تكعيبي.",
      doc_bat_title: "3. تخزين البطاريات (BESS) — حالة الشحن وتدهور SOH",
      doc_bat_desc: "يتتبع حالة الشحن (20%–100%) وكفاءة الشحن والتفريغ وحدود معدل C والتدهور الدوري للسعة.",
      doc_diesel_title: "4. مولد الديزل الاحتياطي وقاعدة الحمل الأدنى 30%",
      doc_diesel_desc: "منحنى استهلاك وقود خطي (Willans) مع حد أدنى 30% لمنع تلف المحرك؛ والفائض يشحن البطارية.",
      doc_fin_title: "5. التحليل المالي (NPC, CRF, LCOE) والموثوقية",
      doc_fin_desc: "يخصم جميع التدفقات النقدية (الاستثمار والصيانة والوقود والاستبدال والقيمة المتبقية) طوال عمر المشروع.",
      doc_csv_title: "6. تنسيق ملفات الطقس المخصصة (CSV / Excel)",
      doc_csv_desc: "يمكنك رفع بياناتك المناخية الخاصة (أو تصدير NASA POWER) من تبويب البيانات والخريطة:",
      doc_csv_note: "تتم معالجة السنوات الكبيسة وتحويل الوحدات من W/m² إلى kW/m² تلقائياً.",
      months: ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
      week_label: "أسبوع",
      best_tag: "الأفضل",
      toast_opt_done: "اكتمل التحسين بالخوارزمية الجينية بنجاح!",
      toast_sim_done: "اكتملت محاكاة 8,760 ساعة.",
      toast_saved: "تم حفظ السيناريو في جدول المقارنة.",
      toast_report_ok: "تم إنشاء التقرير الهندسي بنجاح.",
      toast_upload_ok: "تم استيراد ملف الطقس بنجاح.",
      toast_bench_ok: "تم إنشاء 3 سيناريوهات مرجعية للمقارنة.",
    },
  };

  // ------------------------------------------------------------------------
  // 2. Application State
  // ------------------------------------------------------------------------
  const state = {
    lang: localStorage.getItem("hres_lang") || "fr",
    theme: localStorage.getItem("hres_theme") || "dark",
    activeTab: "data",
    previewMode: "load",
    costViewMode: "npc",
    selectedWeek: 24,
    weatherId: null,
    weatherFilename: null,
    previewData: null,
    currentResult: null,
    lastConvergenceHistory: null,
    scenarios: JSON.parse(localStorage.getItem("hres_scenarios") || "[]"),
    pollTimer: null,
    map: null,
    marker: null,
    tileLayers: {},
    activeMapLayer: "dark",
    charts: {
      preview: null,
      convergence: null,
      dispatch: null,
      monthly: null,
      cost: null,
      cmpLcoe: null,
      cmpNpc: null,
    },
  };

  // ------------------------------------------------------------------------
  // 3. DOM & Formatting Helpers
  // ------------------------------------------------------------------------
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const t = (key) => (I18N[state.lang] && I18N[state.lang][key]) || I18N.en[key] || key;

  function fmtNum(v, decimals = 1) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return "--";
    return Number(v).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function fmtUSD(v, decimals = 0) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return "--";
    const n = Number(v);
    const sign = n < 0 ? "-" : "";
    return `${sign}$${Math.abs(n).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}`;
  }

  function showToast(msg, type = "info") {
    const container = $("#toast-container");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.25s ease";
      setTimeout(() => el.remove(), 260);
    }, 3400);
  }

  function getThemeColors() {
    const isLight = state.theme === "light";
    if (isLight) {
      // Delos Swiss Clinical Luxury Palette
      return {
        text: "#3A3935",
        muted: "#7A7770",
        grid: "#E6E3DB",
        tooltipBg: "#141413",
        tooltipTitle: "#FFFFFF",
        tooltipBody: "#E6E3DB",
        tooltipBorder: "#141413",
        borderBg: "#FFFFFF",
        pv: "#B85D3B",
        pvFill: "rgba(184, 93, 59, 0.12)",
        wind: "#141413",
        windFill: "rgba(20, 20, 19, 0.08)",
        soc: "#7A7770",
        load: "#A6A298",
        loadFill: "rgba(184, 93, 59, 0.10)",
        diesel: "#A83232",
        dieselFill: "rgba(168, 50, 50, 0.15)",
        positive: "#3D6B52",
        positiveFill: "rgba(61, 107, 82, 0.12)",
        secondary: "#141413",
        npcBars: ["#141413", "#7A7770", "#A83232", "#B5B1A6", "#3D6B52"],
        capexSlices: ["#B85D3B", "#141413", "#7A7770", "#A83232"],
      };
    }
    // Rehoboam Noir Palette
    return {
      text: "#D8D6CE",
      muted: "#7A7872",
      grid: "#222228",
      tooltipBg: "#151519",
      tooltipTitle: "#F2F1EC",
      tooltipBody: "#D8D6CE",
      tooltipBorder: "#383842",
      borderBg: "#101013",
      pv: "#D4A359",
      pvFill: "rgba(212, 163, 89, 0.14)",
      wind: "#A8A6A0",
      windFill: "rgba(168, 166, 160, 0.12)",
      soc: "#F2F1EC",
      load: "#78766F",
      loadFill: "rgba(212, 163, 89, 0.12)",
      diesel: "#C24141",
      dieselFill: "rgba(194, 65, 65, 0.18)",
      positive: "#6E9E82",
      positiveFill: "rgba(110, 158, 130, 0.14)",
      secondary: "#F2F1EC",
      npcBars: ["#D4A359", "#A8A6A0", "#C24141", "#52525B", "#6E9E82"],
      capexSlices: ["#D4A359", "#A8A6A0", "#F2F1EC", "#C24141"],
    };
  }

  function chartTooltipStyle(c) {
    return {
      backgroundColor: c.tooltipBg,
      titleColor: c.tooltipTitle,
      bodyColor: c.tooltipBody,
      borderColor: c.tooltipBorder,
      borderWidth: 1,
      cornerRadius: 2,
      padding: 10,
      titleFont: { family: '"IBM Plex Mono", monospace', size: 11, weight: "600" },
      bodyFont: { family: '"IBM Plex Mono", monospace', size: 11 },
    };
  }

  function chartTickFont() {
    return { family: '"IBM Plex Mono", "Cascadia Mono", Consolas, monospace', size: 10.5 };
  }

  function updateTopbarCoords(siteName, lat, lon) {
    const el = $("#topbar-coords");
    if (!el) return;
    const city = (siteName || "SITE").split(",")[0].trim().toUpperCase();
    const latNum = Number(lat) || 0;
    const lonNum = Number(lon) || 0;
    const ns = latNum >= 0 ? "N" : "S";
    const ew = lonNum >= 0 ? "E" : "W";
    el.textContent = `${city} // ${Math.abs(latNum).toFixed(4)}° ${ns}, ${Math.abs(lonNum).toFixed(4)}° ${ew}`;
  }

  // ------------------------------------------------------------------------
  // 4. Localization & Theme Engine
  // ------------------------------------------------------------------------
  function applyLanguage(lang) {
    state.lang = I18N[lang] ? lang : "fr";
    localStorage.setItem("hres_lang", state.lang);
    document.documentElement.lang = state.lang;
    document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";

    $$(".lang-btn").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.lang));
    $$("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (I18N[state.lang][key]) {
        el.textContent = I18N[state.lang][key];
      }
    });

    renderPreviewChart();
    if (state.currentResult) {
      renderResults(state.currentResult, false);
    }
    renderScenarios();
  }

  function applyTheme(theme) {
    state.theme = theme === "light" ? "light" : "dark";
    localStorage.setItem("hres_theme", state.theme);
    document.documentElement.setAttribute("data-theme", state.theme);

    const metaTheme = $("#meta-theme-color");
    if (metaTheme) {
      metaTheme.setAttribute("content", state.theme === "light" ? "#F6F5F0" : "#09090B");
    }

    $("#theme-icon-sun").style.display = state.theme === "dark" ? "block" : "none";
    $("#theme-icon-moon").style.display = state.theme === "light" ? "block" : "none";

    // Sync map layer gently if user is on dark/voyager (respect explicit Satellite selection)
    if (state.map && state.activeMapLayer !== "satellite") {
      setMapLayer(state.theme === "light" ? "voyager" : "dark");
    }

    renderPreviewChart();
    if (state.lastConvergenceHistory && state.lastConvergenceHistory.length > 0) {
      renderConvergenceChart(state.lastConvergenceHistory);
    }
    if (state.currentResult) {
      renderDispatchChart();
      renderMonthlyChart();
      renderCostChart();
    }
    renderScenarioCharts();
  }

  // ------------------------------------------------------------------------
  // 5. Navigation Tabs
  // ------------------------------------------------------------------------
  function switchTab(tabId) {
    state.activeTab = tabId;
    $$(".nav-tab").forEach((btn) => {
      const isAct = btn.dataset.tab === tabId;
      btn.classList.toggle("active", isAct);
      btn.setAttribute("aria-selected", String(isAct));
    });
    $$(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${tabId}`));

    if (tabId === "data" && state.map) {
      setTimeout(() => state.map.invalidateSize(), 100);
    }
    if (tabId === "compare") {
      renderScenarios();
    }
  }

  // ------------------------------------------------------------------------
  // 6. Interactive Leaflet Map (CartoDB Dark Matter / Voyager / Esri Satellite)
  // ------------------------------------------------------------------------
  function initMap() {
    const mapEl = $("#leaflet-map");
    if (typeof window.L === "undefined") {
      mapEl.innerHTML = `
        <div class="map-offline-fallback">
          <strong style="font-size:14px;color:var(--text-primary);margin-bottom:6px;">Offline Map Mode</strong>
          <span>Leaflet tiles unavailable offline. Use GPS coordinates or quick city buttons — all simulations &amp; reports work 100% offline.</span>
        </div>
      `;
      return;
    }

    const lat = parseFloat($("#input-lat").value) || 18.0735;
    const lon = parseFloat($("#input-lon").value) || -15.9582;

    state.map = L.map("leaflet-map", {
      center: [lat, lon],
      zoom: 6,
      zoomControl: true,
    });

    // Zero OpenStreetMap 403 & zero CartoDB API-key watermarks: free Esri ArcGIS basemaps
    state.tileLayers = {
      dark: L.layerGroup([
        L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
          maxZoom: 16,
          attribution: "Tiles &copy; Esri",
        }),
        L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}", {
          maxZoom: 16,
        }),
      ]),
      voyager: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 18,
        attribution: "Tiles &copy; Esri",
      }),
      satellite: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 18,
        attribution: "Tiles &copy; Esri",
      }),
    };

    const initialLayer = state.theme === "light" ? "voyager" : "dark";
    setMapLayer(initialLayer);

    const reticleIcon = L.divIcon({
      className: "hres-reticle-icon",
      html: '<div class="hres-reticle"><span class="hres-reticle-ring"></span></div>',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    state.marker = L.marker([lat, lon], { icon: reticleIcon }).addTo(state.map);

    state.map.on("click", (e) => {
      const clickLat = Number(e.latlng.lat.toFixed(4));
      const clickLon = Number(e.latlng.lng.toFixed(4));
      $("#input-lat").value = clickLat;
      $("#input-lon").value = clickLon;
      $("#input-site-name").value = `Site (${clickLat}°, ${clickLon}°)`;
      $$("#city-pills .pill").forEach((p) => p.classList.remove("active"));
      updateMapMarker(clickLat, clickLon, false);
      clearUploadedWeather(false);
      fetchPreview();
    });
  }

  function setMapLayer(layerKey) {
    if (!state.map || !state.tileLayers[layerKey]) return;
    Object.values(state.tileLayers).forEach((lyr) => {
      if (state.map.hasLayer(lyr)) state.map.removeLayer(lyr);
    });
    state.tileLayers[layerKey].addTo(state.map);
    state.activeMapLayer = layerKey;
    const wrapper = $(".map-wrapper");
    if (wrapper) {
      wrapper.classList.toggle("map-layer-satellite", layerKey === "satellite");
    }
    $$(".map-layer-btn").forEach((b) => b.classList.toggle("active", b.dataset.layer === layerKey));
  }

  function updateMapMarker(lat, lon, pan = true) {
    if (!state.map || !state.marker) return;
    state.marker.setLatLng([lat, lon]);
    if (pan) state.map.setView([lat, lon], Math.max(state.map.getZoom(), 6), { animate: true });
  }

  // ------------------------------------------------------------------------
  // 7. Payload Builders
  // ------------------------------------------------------------------------
  function getCostParams() {
    return {
      pv_capex: parseFloat($("#cost-pv-capex").value) || 1000,
      wind_capex: parseFloat($("#cost-wind-capex").value) || 1600,
      battery_capex: parseFloat($("#cost-bat-capex").value) || 300,
      diesel_capex: parseFloat($("#cost-diesel-capex").value) || 400,
      diesel_fuel_price: parseFloat($("#cost-fuel-price").value) || 1.3,
      discount_rate: (parseFloat($("#cost-discount-rate").value) || 8.0) / 100.0,
      project_lifetime: parseInt($("#cost-lifetime").value, 10) || 25,
    };
  }

  function getSiteAndLoadPayload() {
    return {
      latitude: parseFloat($("#input-lat").value) || 18.0735,
      longitude: parseFloat($("#input-lon").value) || -15.9582,
      site_name: $("#input-site-name").value.trim() || "Nouakchott, Mauritania",
      project_name: `${$("#input-site-name").value.trim() || "Microgrid"} — HRES Study`,
      year: parseInt($("#input-year").value, 10) || 2023,
      weather_source: $("#select-weather-source").value || "synthetic",
      weather_id: state.weatherId,
      households: parseInt($("#slider-households").value, 10) || 60,
      school_preset: $("#select-school").value || "medium",
      clinic_preset: $("#select-clinic").value || "small",
    };
  }

  // ------------------------------------------------------------------------
  // 8. API Calls: Health, Preview, Weather Upload
  // ------------------------------------------------------------------------
  async function checkHealth() {
    try {
      const resp = await fetch("/api/health");
      if (!resp.ok) throw new Error("API error");
      const data = await resp.json();
      $("#api-status-text").textContent = data.pygad_available ? "FastNumPy · PyGAD" : "FastNumPy GA";
    } catch {
      $("#api-status-text").textContent = "Offline";
    }
  }

  let previewDebounce = null;
  function schedulePreview() {
    clearTimeout(previewDebounce);
    previewDebounce = setTimeout(fetchPreview, 220);
  }

  async function fetchPreview() {
    const payload = getSiteAndLoadPayload();
    $("#map-source-subtitle").textContent = `${payload.site_name} · ${payload.latitude.toFixed(4)}°N, ${payload.longitude.toFixed(4)}°E`;
    updateTopbarCoords(payload.site_name, payload.latitude, payload.longitude);
    try {
      const resp = await fetch("/api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Preview failed");
      }
      const data = await resp.json();
      state.previewData = data;
      updatePreviewUI(data);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function updatePreviewUI(data) {
    const s = data.summary;
    $("#stat-annual-load").textContent = `${fmtNum(s.annual_demand_kwh / 1000, 1)} MWh`;
    $("#stat-peak-load").textContent = `${fmtNum(s.peak_load_kw, 1)} kW`;
    $("#stat-ghi").textContent = `${fmtNum(s.avg_ghi_kwh_m2_day, 2)} kWh/m²/d`;
    $("#stat-wind").textContent = `${fmtNum(s.avg_wind_ms, 2)} m/s`;

    const badgeMap = {
      synthetic: "SYNTHETIC 8760H",
      synthetic_fallback: "OFFLINE FALLBACK",
      nasa_cache: "NASA POWER (CACHE)",
      nasa_api: "NASA POWER (LIVE)",
      custom_upload: `CUSTOM: ${data.filename || "CSV"}`,
    };
    $("#weather-source-pill").textContent = badgeMap[data.weather_source] || data.weather_source.toUpperCase();
    renderPreviewChart();
  }

  async function handleWeatherFileUpload(file) {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const base = getSiteAndLoadPayload();
    const qs = new URLSearchParams({
      year: String(base.year),
      households: String(base.households),
      school_preset: base.school_preset,
      clinic_preset: base.clinic_preset,
    });

    try {
      const resp = await fetch(`/api/upload-weather?${qs.toString()}`, {
        method: "POST",
        body: form,
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Upload failed");

      state.weatherId = data.weather_id;
      state.weatherFilename = data.filename;
      state.previewData = data;
      $("#upload-status-text").textContent = `✓ ${data.filename} — ${data.parse_note}`;
      $("#upload-status-badge").style.display = "flex";
      updatePreviewUI(data);
      showToast(t("toast_upload_ok"), "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function clearUploadedWeather(refresh = true) {
    state.weatherId = null;
    state.weatherFilename = null;
    $("#upload-status-badge").style.display = "none";
    $("#weather-file-input").value = "";
    if (refresh) fetchPreview();
  }

  // ------------------------------------------------------------------------
  // 9. Chart Helpers (with Offline Guard)
  // ------------------------------------------------------------------------
  function hasChartJs(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return false;
    const fallback = canvas.parentElement.querySelector(".chart-offline-msg");
    if (typeof window.Chart === "undefined") {
      canvas.style.display = "none";
      if (fallback) fallback.style.display = "flex";
      return false;
    }
    canvas.style.display = "block";
    if (fallback) fallback.style.display = "none";
    return true;
  }

  function destroyChart(key) {
    if (state.charts[key]) {
      state.charts[key].destroy();
      state.charts[key] = null;
    }
  }

  function renderPreviewChart() {
    if (!state.previewData || !hasChartJs("chart-preview")) return;
    destroyChart("preview");

    const ctx = $("#chart-preview").getContext("2d");
    const c = getThemeColors();
    const months = t("months");
    const tickFont = chartTickFont();
    const tooltipCfg = chartTooltipStyle(c);

    if (state.previewMode === "load") {
      const p7 = state.previewData.preview_7d;
      state.charts.preview = new Chart(ctx, {
        type: "line",
        data: {
          labels: p7.hours.map((h) => `D${Math.floor(h / 24) + 1} ${String(h % 24).padStart(2, "0")}h`),
          datasets: [
            {
              label: "Total Load (kW)",
              data: p7.load_kw,
              borderColor: c.pv,
              backgroundColor: c.loadFill,
              fill: true,
              borderWidth: 1.75,
              pointRadius: 0,
              tension: 0.28,
            },
            {
              label: "Households (kW)",
              data: p7.household_kw,
              borderColor: c.soc,
              borderDash: [4, 4],
              borderWidth: 1.4,
              pointRadius: 0,
              tension: 0.28,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: {
            legend: { labels: { color: c.text, boxWidth: 12, boxHeight: 2, font: tickFont } },
            tooltip: tooltipCfg,
          },
          scales: {
            x: { ticks: { color: c.muted, maxTicksLimit: 10, font: tickFont }, grid: { color: c.grid } },
            y: { beginAtZero: true, title: { display: true, text: "kW", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
          },
        },
      });
    } else if (state.previewMode === "solar") {
      state.charts.preview = new Chart(ctx, {
        type: "bar",
        data: {
          labels: months,
          datasets: [
            {
              label: "Daily GHI (kWh/m²/day)",
              data: state.previewData.monthly.ghi_daily_kwh_m2,
              backgroundColor: c.pv,
              borderColor: c.pv,
              borderRadius: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: c.text, boxWidth: 10, font: tickFont } },
            tooltip: tooltipCfg,
          },
          scales: {
            x: { ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
            y: { beginAtZero: true, title: { display: true, text: "kWh/m²/day", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
          },
        },
      });
    } else {
      state.charts.preview = new Chart(ctx, {
        type: "bar",
        data: {
          labels: months,
          datasets: [
            {
              label: "Mean Wind Speed (m/s @ 10m)",
              data: state.previewData.monthly.wind_avg_ms,
              backgroundColor: c.wind,
              borderColor: c.wind,
              borderRadius: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: c.text, boxWidth: 10, font: tickFont } },
            tooltip: tooltipCfg,
          },
          scales: {
            x: { ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
            y: { beginAtZero: true, title: { display: true, text: "m/s", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
          },
        },
      });
    }
  }

  function renderConvergenceChart(fitnessHistory) {
    state.lastConvergenceHistory = fitnessHistory;
    if (!hasChartJs("chart-convergence")) return;
    destroyChart("convergence");
    const ctx = $("#chart-convergence").getContext("2d");
    const c = getThemeColors();
    const tickFont = chartTickFont();
    const lcoeSeries = (fitnessHistory || []).map((f) => (f > 1e-6 ? Number((1.0 / f).toFixed(4)) : null));
    const labels = lcoeSeries.map((_, i) => `G${i + 1}`);

    state.charts.convergence = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Best LCOE ($/kWh)",
            data: lcoeSeries,
            borderColor: c.pv,
            backgroundColor: c.pvFill,
            fill: true,
            borderWidth: 1.75,
            pointRadius: 2,
            pointBackgroundColor: c.pv,
            tension: 0.25,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { labels: { color: c.text, boxWidth: 12, boxHeight: 2, font: tickFont } },
          tooltip: chartTooltipStyle(c),
        },
        scales: {
          x: { ticks: { color: c.muted, maxTicksLimit: 10, font: tickFont }, grid: { color: c.grid } },
          y: { title: { display: true, text: "$/kWh", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
        },
      },
    });
  }

  // ------------------------------------------------------------------------
  // 10. GA Optimization (Async Job Polling) & Manual Simulation
  // ------------------------------------------------------------------------
  async function startOptimization() {
    const btn = $("#btn-run-optimize");
    btn.disabled = true;
    clearInterval(state.pollTimer);

    const payload = {
      ...getSiteAndLoadPayload(),
      enable_pv: $("#toggle-pv").checked,
      enable_wind: $("#toggle-wind").checked,
      enable_battery: $("#toggle-battery").checked,
      enable_diesel: $("#toggle-diesel").checked,
      pv_min: parseFloat($("#bound-pv-min").value) || 0,
      pv_max: parseFloat($("#bound-pv-max").value) || 250,
      wind_min: parseFloat($("#bound-wind-min").value) || 0,
      wind_max: parseFloat($("#bound-wind-max").value) || 100,
      battery_min: parseFloat($("#bound-bat-min").value) || 0,
      battery_max: parseFloat($("#bound-bat-max").value) || 600,
      diesel_min: parseFloat($("#bound-diesel-min").value) || 0,
      diesel_max: parseFloat($("#bound-diesel-max").value) || 60,
      lolp_max: (parseFloat($("#slider-lolp").value) || 1.0) / 100.0,
      num_generations: parseInt($("#input-ga-gens").value, 10) || 25,
      sol_per_pop: parseInt($("#input-ga-pop").value, 10) || 16,
      cost_params: getCostParams(),
    };

    $("#opt-state-badge").textContent = "RUNNING";
    $("#opt-progress-bar").style.width = "3%";
    $("#opt-progress-text").textContent = "3%";
    $("#opt-console").textContent = "Submitting GA optimization job...";

    try {
      const resp = await fetch("/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Optimization failed to start");

      const jobId = data.job_id;
      state.pollTimer = setInterval(() => pollJob(jobId), 300);
      pollJob(jobId);
    } catch (err) {
      btn.disabled = false;
      $("#opt-state-badge").textContent = "ERROR";
      showToast(err.message, "error");
    }
  }

  async function pollJob(jobId) {
    try {
      const resp = await fetch(`/api/jobs/${jobId}`);
      if (!resp.ok) throw new Error("Failed to poll job status");
      const job = await resp.json();

      $("#opt-progress-bar").style.width = `${job.progress_pct}%`;
      $("#opt-progress-text").textContent = `${fmtNum(job.progress_pct, 0)}%`;
      $("#opt-gen-text").textContent = `${job.current_generation} / ${job.total_generations}`;
      $("#opt-elapsed-text").textContent = `${fmtNum(job.elapsed_sec, 1)}s`;
      if (job.best_lcoe !== null && job.best_lcoe !== undefined) {
        $("#opt-best-lcoe").textContent = `$${fmtNum(job.best_lcoe, 4)}/kWh`;
      }

      const consoleEl = $("#opt-console");
      consoleEl.textContent = (job.logs || []).join("\n");
      consoleEl.scrollTop = consoleEl.scrollHeight;

      if (job.convergence_history && job.convergence_history.length > 0) {
        renderConvergenceChart(job.convergence_history);
      }

      if (job.status === "completed") {
        clearInterval(state.pollTimer);
        $("#btn-run-optimize").disabled = false;
        $("#opt-state-badge").textContent = "COMPLETED";
        if (job.result) {
          state.currentResult = job.result;
          syncManualInputsFromConfig(job.result.best_configuration);
          renderResults(job.result, true);
          showToast(t("toast_opt_done"), "success");
          switchTab("results");
        }
      } else if (job.status === "failed") {
        clearInterval(state.pollTimer);
        $("#btn-run-optimize").disabled = false;
        $("#opt-state-badge").textContent = "FAILED";
        showToast(job.error || "Optimization failed", "error");
      }
    } catch (err) {
      clearInterval(state.pollTimer);
      $("#btn-run-optimize").disabled = false;
      showToast(err.message, "error");
    }
  }

  function syncManualInputsFromConfig(cfg) {
    if (!cfg) return;
    $("#manual-pv").value = Number(cfg.pv_capacity || 0).toFixed(1);
    $("#manual-wind").value = Number(cfg.wind_capacity || 0).toFixed(1);
    $("#manual-battery").value = Number(cfg.battery_capacity || 0).toFixed(1);
    $("#manual-diesel").value = Number(cfg.diesel_capacity || 0).toFixed(1);
  }

  async function runManualSimulation(switchToResults = true, customCaps = null) {
    const btn = $("#btn-run-manual");
    if (btn) btn.disabled = true;

    const payload = {
      ...getSiteAndLoadPayload(),
      pv_capacity: customCaps ? customCaps.pv_capacity : (parseFloat($("#manual-pv").value) || 0),
      wind_capacity: customCaps ? customCaps.wind_capacity : (parseFloat($("#manual-wind").value) || 0),
      battery_capacity: customCaps ? customCaps.battery_capacity : (parseFloat($("#manual-battery").value) || 0),
      diesel_capacity: customCaps ? customCaps.diesel_capacity : (parseFloat($("#manual-diesel").value) || 0),
      cost_params: getCostParams(),
    };

    try {
      const resp = await fetch("/api/simulate-manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "Simulation failed");

      if (!customCaps) {
        state.currentResult = data;
        renderResults(data, true);
        if (switchToResults) {
          showToast(t("toast_sim_done"), "success");
          switchTab("results");
        }
      }
      return data;
    } catch (err) {
      showToast(err.message, "error");
      return null;
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  // ------------------------------------------------------------------------
  // 11. Results Rendering (KPIs, Sizing, Week 1-52 Dispatch, Monthly, Cost, Tables)
  // ------------------------------------------------------------------------
  function renderResults(res, updateNamePlaceholder = true) {
    if (!res) return;
    const cfg = res.best_configuration;
    const m = res.metrics;
    const fin = res.financial_details || {};
    const meta = res.metadata || {};

    $("#res-site-heading").textContent = meta.site_name || "HRES Microgrid";
    $("#res-method-badge").textContent = res.optimization_method || "Simulation";
    $("#res-meta-subtitle").textContent = `${fmtNum(meta.latitude, 4)}°N, ${fmtNum(meta.longitude, 4)}°E · ${meta.households ?? "--"} HH · ${fin.project_lifetime || 25} yrs @ ${fmtNum((fin.discount_rate || 0.08) * 100, 1)}%`;

    if (updateNamePlaceholder) {
      const archTags = [];
      if (cfg.pv_capacity > 0.5) archTags.push("PV");
      if (cfg.wind_capacity > 0.5) archTags.push("Wind");
      if (cfg.battery_capacity > 0.5) archTags.push("BESS");
      if (cfg.diesel_capacity > 0.5) archTags.push("Diesel");
      $("#input-scenario-name").value = `${archTags.join("+") || "Custom"} (${(meta.site_name || "Site").split(",")[0]})`;
    }

    // 8 Executive KPIs
    $("#kpi-lcoe").textContent = `$${fmtNum(m.lcoe, 4)}/kWh`;
    $("#kpi-lcoe-sub").textContent = `${fmtNum(m.served_load_kwh / 1000, 1)} MWh/yr served`;

    $("#kpi-npc").textContent = fmtUSD(m.npc);
    $("#kpi-npc-sub").textContent = `${fin.project_lifetime || 25} yrs @ ${fmtNum((fin.discount_rate || 0.08) * 100, 1)}%`;

    $("#kpi-capex").textContent = fmtUSD(m.capital_cost);
    $("#kpi-opex-sub").textContent = `OPEX: ${fmtUSD(m.annual_om_cost)}/yr`;

    $("#kpi-rf").textContent = `${fmtNum(m.renewable_fraction * 100, 1)}%`;
    $("#kpi-rf-sub").textContent = `PV ${fmtNum(m.total_pv_generation_kwh / 1000, 1)} + Wind ${fmtNum(m.total_wind_generation_kwh / 1000, 1)} MWh`;

    $("#kpi-reliability").textContent = `${fmtNum(m.reliability_pct, 2)}%`;
    $("#kpi-lolp-sub").textContent = `LOLP: ${fmtNum(m.lolp * 100, 2)}% · ${m.capacity_shortage_hours} h`;

    $("#kpi-fuel").textContent = `${fmtNum(m.fuel_consumption_liters, 0)} L/yr`;
    $("#kpi-fuel-sub").textContent = `${fmtNum(m.diesel_operating_hours, 0)} h/yr · ${fmtUSD(m.annual_fuel_cost)}/yr`;

    $("#kpi-co2").textContent = `${fmtNum(m.annual_co2_avoided_tons, 1)} t/yr`;
    $("#kpi-co2-sub").textContent = `${fmtNum(m.lifetime_co2_avoided_tons, 0)} tCO₂ (${fin.project_lifetime || 25} yrs)`;

    $("#kpi-soh").textContent = cfg.battery_capacity > 0 ? `${fmtNum(m.battery_soh_pct, 1)}%` : "N/A";
    $("#kpi-soh-sub").textContent = fin.battery_lifetime_years ? `Est. life: ${fmtNum(fin.battery_lifetime_years, 1)} yrs` : "No battery";

    // Optimal Sizing Cards
    const totCapex = Math.max(1, fin.capital_cost || 1);
    const pvPct = ((fin.pv_capital || 0) / totCapex) * 100;
    const windPct = ((fin.wind_capital || 0) / totCapex) * 100;
    const batPct = ((fin.battery_capital || 0) / totCapex) * 100;
    const dieselPct = ((fin.diesel_capital || 0) / totCapex) * 100;

    $("#arch-pv-val").textContent = `${fmtNum(cfg.pv_capacity, 1)} kWp`;
    $("#arch-pv-sub").textContent = `CAPEX: ${fmtUSD(fin.pv_capital)} (${fmtNum(pvPct, 1)}%)`;
    $("#arch-pv-bar").style.width = `${pvPct}%`;

    $("#arch-wind-val").textContent = `${fmtNum(cfg.wind_capacity, 1)} kW`;
    $("#arch-wind-sub").textContent = `CAPEX: ${fmtUSD(fin.wind_capital)} (${fmtNum(windPct, 1)}%)`;
    $("#arch-wind-bar").style.width = `${windPct}%`;

    $("#arch-bat-val").textContent = `${fmtNum(cfg.battery_capacity, 1)} kWh`;
    $("#arch-bat-sub").textContent = `CAPEX: ${fmtUSD(fin.battery_capital)} (${fmtNum(batPct, 1)}%)`;
    $("#arch-bat-bar").style.width = `${batPct}%`;

    $("#arch-diesel-val").textContent = `${fmtNum(cfg.diesel_capacity, 1)} kW`;
    $("#arch-diesel-sub").textContent = `CAPEX: ${fmtUSD(fin.diesel_capital)} (${fmtNum(dieselPct, 1)}%)`;
    $("#arch-diesel-bar").style.width = `${dieselPct}%`;

    // Detailed Summary Tables (Always visible, 100% offline safe)
    const energyRows = [
      ["Total Annual Demand", `${fmtNum(m.total_load_kwh, 0)} kWh (${fmtNum(m.total_load_kwh / 1000, 1)} MWh)`],
      ["Energy Served", `${fmtNum(m.served_load_kwh, 0)} kWh (${fmtNum(m.reliability_pct, 2)}%)`],
      ["Solar PV Generation", `${fmtNum(m.total_pv_generation_kwh, 0)} kWh`],
      ["Wind Generation", `${fmtNum(m.total_wind_generation_kwh, 0)} kWh`],
      ["Diesel Generation", `${fmtNum(m.total_diesel_generation_kwh, 0)} kWh (${fmtNum(m.diesel_operating_hours, 0)} h)`],
      ["Curtailed / Excess Energy", `${fmtNum(m.total_dump_power_kwh, 0)} kWh`],
      ["Unmet Load", `${fmtNum(m.unmet_load_kwh, 0)} kWh (${m.capacity_shortage_hours} h)`],
      ["Annual Hybrid CO₂ Emissions", `${fmtNum(m.annual_co2_hybrid_tons, 2)} tCO₂/yr`],
      ["Annual CO₂ Avoided (vs. 100% Diesel)", `${fmtNum(m.annual_co2_avoided_tons, 2)} tCO₂/yr`],
    ];
    $("#tbody-energy-summary").innerHTML = energyRows
      .map(([k, v]) => `<tr><td>${k}</td><td class="num"><strong>${v}</strong></td></tr>`)
      .join("");

    const finRows = [
      ["Initial Capital Cost (CAPEX)", fmtUSD(fin.capital_cost)],
      ["Discounted Fixed O&M", fmtUSD(fin.discounted_fixed_om)],
      ["Discounted Diesel Fuel", fmtUSD(fin.discounted_fuel)],
      ["Discounted Replacements", fmtUSD(fin.discounted_replacement)],
      ["Discounted Salvage Credit", `-${fmtUSD(fin.discounted_salvage)}`],
      ["Total Net Present Cost (NPC)", fmtUSD(fin.npc)],
      ["Equivalent Annualized Cost", `${fmtUSD(fin.annualized_cost)} / yr`],
      ["Levelized Cost of Energy (LCOE)", `$${fmtNum(m.lcoe, 4)} / kWh`],
    ];
    $("#tbody-fin-summary").innerHTML = finRows
      .map(([k, v], i) => `<tr style="${i >= 5 ? "font-weight:700;" : ""}"><td>${k}</td><td class="num">${v}</td></tr>`)
      .join("");

    renderEnergyMixRing(res);
    renderDispatchChart();
    renderMonthlyChart();
    renderCostChart();
  }

  function renderEnergyMixRing(res) {
    if (!res || !res.metrics) return;
    const m = res.metrics;
    const rfPct = Math.max(0, Math.min(100, (m.renewable_fraction || 0) * 100));
    const pvGen = Math.max(0, m.total_pv_generation_kwh || 0);
    const windGen = Math.max(0, m.total_wind_generation_kwh || 0);
    const dieselGen = Math.max(0, m.total_diesel_generation_kwh || 0);
    const totalGen = Math.max(1e-6, pvGen + windGen + dieselGen);
    const served = Math.max(1e-6, m.served_load_kwh || m.total_load_kwh || 1);

    const pvPct = Math.max(0, Math.min(100, (pvGen / totalGen) * 100));
    const windPct = Math.max(0, Math.min(100, (windGen / totalGen) * 100));
    // Half of round-trip battery throughput represents energy discharged from BESS to load
    const bessDisPct = Math.max(0, Math.min(100, (((m.battery_total_throughput_kwh || 0) * 0.5) / served) * 100));
    const dieselPct = Math.max(0, Math.min(100, (dieselGen / served) * 100));

    const rfEl = $("#mix-rf-center");
    if (rfEl) rfEl.textContent = `${fmtNum(rfPct, 1)}%`;

    const setArc = (id, radius, pct) => {
      const el = $(id);
      if (!el) return;
      const circ = 2 * Math.PI * radius;
      const clamped = Math.max(0, Math.min(100, pct));
      el.style.strokeDasharray = `${circ.toFixed(2)}`;
      el.style.strokeDashoffset = `${(circ * (1 - clamped / 100)).toFixed(2)}`;
    };

    setArc("#ring-pv", 98, pvPct);
    setArc("#ring-bess", 84, bessDisPct);
    setArc("#ring-wind", 71, windPct);
    setArc("#ring-diesel", 59, dieselPct);

    const setVal = (id, pct) => {
      const el = $(id);
      if (el) el.textContent = `${fmtNum(pct, 1)}%`;
    };
    setVal("#mix-pct-pv", pvPct);
    setVal("#mix-pct-bess", bessDisPct);
    setVal("#mix-pct-wind", windPct);
    setVal("#mix-pct-diesel", dieselPct);
  }

  function getWeekDateRange(weekNum, year = 2023) {
    const startDay = (weekNum - 1) * 7;
    const d1 = new Date(Date.UTC(year, 0, 1 + startDay));
    const d2 = new Date(Date.UTC(year, 0, 1 + startDay + 6));
    const fmt = (d) => d.toLocaleDateString("en-US", { month: "short", day: "2-digit", timeZone: "UTC" });
    return `${fmt(d1)} – ${fmt(d2)}`;
  }

  function renderDispatchChart() {
    if (!state.currentResult || !state.currentResult.hourly_dispatch) return;
    const week = Math.max(1, Math.min(52, state.selectedWeek));
    const year = (state.currentResult.metadata && state.currentResult.metadata.year) || 2023;
    $("#week-badge").textContent = `${t("week_label")} ${week} · ${getWeekDateRange(week, year)}`;
    $("#slider-week").value = week;

    if (!hasChartJs("chart-dispatch")) return;
    destroyChart("dispatch");

    const hd = state.currentResult.hourly_dispatch;
    const startH = Math.min(hd.load.length - 168, (week - 1) * 168);
    const endH = Math.min(hd.load.length, startH + 168);

    const labels = [];
    for (let h = 0; h < endH - startH; h++) {
      const d = Math.floor(h / 24) + 1;
      const hr = h % 24;
      labels.push(hr === 0 ? `Day ${d}` : `D${d} ${String(hr).padStart(2, "0")}h`);
    }

    const c = getThemeColors();
    const tickFont = chartTickFont();
    const ctx = $("#chart-dispatch").getContext("2d");

    state.charts.dispatch = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Solar PV (kW)",
            data: hd.pv.slice(startH, endH),
            borderColor: c.pv,
            backgroundColor: c.pvFill,
            fill: true,
            borderWidth: 1.75,
            pointRadius: 0,
            tension: 0.25,
            yAxisID: "y",
          },
          {
            label: "Wind (kW)",
            data: hd.wind.slice(startH, endH),
            borderColor: c.wind,
            backgroundColor: c.windFill,
            fill: false,
            borderWidth: 1.6,
            pointRadius: 0,
            tension: 0.25,
            yAxisID: "y",
          },
          {
            label: "Diesel (kW)",
            data: hd.diesel.slice(startH, endH),
            borderColor: c.diesel,
            backgroundColor: c.dieselFill,
            fill: true,
            borderWidth: 1.5,
            pointRadius: 0,
            tension: 0.1,
            yAxisID: "y",
          },
          {
            label: "Load Demand (kW)",
            data: hd.load.slice(startH, endH),
            borderColor: c.load,
            borderDash: [5, 4],
            borderWidth: 1.75,
            pointRadius: 0,
            tension: 0.25,
            yAxisID: "y",
          },
          {
            label: "Battery SOC (%)",
            data: hd.soc_pct.slice(startH, endH),
            borderColor: c.soc,
            borderWidth: 1.85,
            pointRadius: 0,
            tension: 0.25,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "top", labels: { color: c.text, boxWidth: 14, boxHeight: 2, padding: 14, font: tickFont } },
          tooltip: chartTooltipStyle(c),
        },
        scales: {
          x: { ticks: { color: c.muted, maxTicksLimit: 14, font: tickFont }, grid: { color: c.grid } },
          y: {
            type: "linear",
            position: "left",
            beginAtZero: true,
            title: { display: true, text: "Power (kW)", color: c.muted, font: tickFont },
            ticks: { color: c.muted, font: tickFont },
            grid: { color: c.grid },
          },
          y1: {
            type: "linear",
            position: "right",
            min: 0,
            max: 100,
            title: { display: true, text: "Battery SOC (%)", color: c.soc, font: tickFont },
            ticks: { color: c.soc, font: tickFont, stepSize: 20 },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }

  function renderMonthlyChart() {
    if (!state.currentResult || !hasChartJs("chart-monthly")) return;
    destroyChart("monthly");
    const mb = state.currentResult.monthly_balance;
    const c = getThemeColors();
    const tickFont = chartTickFont();
    const ctx = $("#chart-monthly").getContext("2d");

    state.charts.monthly = new Chart(ctx, {
      data: {
        labels: t("months"),
        datasets: [
          { type: "bar", label: "Solar PV (MWh)", data: mb.pv_mwh, backgroundColor: c.pv, stack: "gen", borderRadius: 1 },
          { type: "bar", label: "Wind (MWh)", data: mb.wind_mwh, backgroundColor: c.wind, stack: "gen", borderRadius: 1 },
          { type: "bar", label: "Diesel (MWh)", data: mb.diesel_mwh, backgroundColor: c.diesel, stack: "gen", borderRadius: 1 },
          { type: "line", label: "Demand (MWh)", data: mb.load_mwh, borderColor: c.soc, backgroundColor: c.soc, borderDash: [4, 3], borderWidth: 1.85, pointRadius: 2.5, tension: 0.25 },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: c.text, boxWidth: 10, font: tickFont } },
          tooltip: chartTooltipStyle(c),
        },
        scales: {
          x: { stacked: true, ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, title: { display: true, text: "MWh / month", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
        },
      },
    });
  }

  function renderCostChart() {
    if (!state.currentResult || !hasChartJs("chart-cost")) return;
    destroyChart("cost");
    const fin = state.currentResult.financial_details || {};
    const c = getThemeColors();
    const tickFont = chartTickFont();
    const ctx = $("#chart-cost").getContext("2d");

    if (state.costViewMode === "npc") {
      const vals = [
        fin.capital_cost || 0,
        fin.discounted_fixed_om || 0,
        fin.discounted_fuel || 0,
        fin.discounted_replacement || 0,
        -(fin.discounted_salvage || 0),
      ];
      state.charts.cost = new Chart(ctx, {
        type: "bar",
        data: {
          labels: ["CAPEX", "Fixed O&M", "Fuel", "Replacement", "Salvage"],
          datasets: [
            {
              label: "Present Value ($ USD)",
              data: vals,
              backgroundColor: c.npcBars,
              borderRadius: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: chartTooltipStyle(c),
          },
          scales: {
            x: { ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
            y: { ticks: { color: c.muted, font: tickFont, callback: (v) => `$${(v / 1000).toFixed(0)}k` }, grid: { color: c.grid } },
          },
        },
      });
    } else {
      const items = [
        ["Solar PV", fin.pv_capital || 0, c.capexSlices[0]],
        ["Wind", fin.wind_capital || 0, c.capexSlices[1]],
        ["Battery (BESS)", fin.battery_capital || 0, c.capexSlices[2]],
        ["Diesel", fin.diesel_capital || 0, c.capexSlices[3]],
      ].filter((x) => x[1] > 0);

      state.charts.cost = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: items.map((x) => x[0]),
          datasets: [{ data: items.map((x) => x[1]), backgroundColor: items.map((x) => x[2]), borderWidth: 2, borderColor: c.borderBg }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "66%",
          plugins: {
            legend: { position: "bottom", labels: { color: c.text, padding: 14, boxWidth: 10, font: tickFont } },
            tooltip: chartTooltipStyle(c),
          },
        },
      });
    }
  }

  // ------------------------------------------------------------------------
  // 12. Bankable Report Export (HTML/PDF via /api/report)
  // ------------------------------------------------------------------------
  async function exportReport(download = false) {
    if (!state.currentResult) {
      showToast("Run a simulation or optimization first.", "warning");
      return;
    }
    const btn = $("#btn-export-report");
    btn.disabled = true;

    try {
      const resp = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: state.currentResult.run_id,
          language: state.lang,
          sample_week_start_day: (state.selectedWeek - 1) * 7 + 1,
          download,
          site_name: $("#input-site-name").value.trim() || undefined,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || "Report generation failed");
      }
      const html = await resp.text();
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);

      if (download) {
        const a = document.createElement("a");
        a.href = url;
        a.download = `HRES_Bankable_Report_${state.lang.toUpperCase()}.html`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      } else {
        window.open(url, "_blank", "noopener");
      }
      showToast(t("toast_report_ok"), "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
    }
  }

  // ------------------------------------------------------------------------
  // 13. Scenario Comparator (Save, Benchmarks, Charts, CSV Export)
  // ------------------------------------------------------------------------
  function persistScenarios() {
    localStorage.setItem("hres_scenarios", JSON.stringify(state.scenarios));
  }

  function saveCurrentScenario(customName = null, resObj = null) {
    const res = resObj || state.currentResult;
    if (!res) return;
    const cfg = res.best_configuration;
    const m = res.metrics;
    const name = customName || $("#input-scenario-name").value.trim() || `Scenario #${state.scenarios.length + 1}`;

    state.scenarios.push({
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name,
      site: (res.metadata && res.metadata.site_name) || "Site",
      pv: cfg.pv_capacity,
      wind: cfg.wind_capacity,
      battery: cfg.battery_capacity,
      diesel: cfg.diesel_capacity,
      lcoe: m.lcoe,
      npc: m.npc,
      capex: m.capital_cost,
      rf: m.renewable_fraction * 100,
      lolp: m.lolp * 100,
      co2_avoided: m.annual_co2_avoided_tons,
    });
    persistScenarios();
    renderScenarios();
    if (!customName) showToast(t("toast_saved"), "success");
  }

  async function generateBenchmarks() {
    const btn = $("#btn-gen-benchmarks");
    btn.disabled = true;
    const siteShort = ($("#input-site-name").value.trim() || "Site").split(",")[0];
    const peak = (state.previewData && state.previewData.summary && state.previewData.summary.peak_load_kw) || 40;
    const specs = [
      { name: `100% Diesel Baseline (${siteShort})`, caps: { pv_capacity: 0, wind_capacity: 0, battery_capacity: 0, diesel_capacity: Math.ceil(peak * 1.15) } },
      { name: `Solar PV + BESS Only (${siteShort})`, caps: { pv_capacity: Math.round(peak * 3.6), wind_capacity: 0, battery_capacity: Math.round(peak * 10.5), diesel_capacity: 0 } },
      { name: `Hybrid PV+Wind+BESS+Diesel (${siteShort})`, caps: { pv_capacity: Math.round(peak * 2.8), wind_capacity: Math.round(peak * 0.35), battery_capacity: Math.round(peak * 7.2), diesel_capacity: Math.round(peak * 0.35) } },
    ];

    try {
      for (const s of specs) {
        const res = await runManualSimulation(false, s.caps);
        if (res) saveCurrentScenario(s.name, res);
      }
      showToast(t("toast_bench_ok"), "success");
    } finally {
      btn.disabled = false;
    }
  }

  function renderScenarios() {
    const tbody = $("#tbody-scenarios");
    const empty = $("#cmp-empty-state");
    if (!state.scenarios.length) {
      tbody.innerHTML = "";
      empty.style.display = "block";
      destroyChart("cmpLcoe");
      destroyChart("cmpNpc");
      return;
    }
    empty.style.display = "none";

    const bestLcoe = Math.min(...state.scenarios.map((s) => s.lcoe));
    const bestRf = Math.max(...state.scenarios.map((s) => s.rf));

    tbody.innerHTML = state.scenarios
      .map((s) => {
        const lcoeBadge = Math.abs(s.lcoe - bestLcoe) < 1e-6 ? `<span class="best-pill">${t("best_tag")}</span>` : "";
        const rfBadge = Math.abs(s.rf - bestRf) < 1e-4 && s.rf > 0 ? `<span class="best-pill">${t("best_tag")}</span>` : "";
        return `
          <tr>
            <td><strong>${s.name}</strong></td>
            <td class="num">${fmtNum(s.pv, 1)}</td>
            <td class="num">${fmtNum(s.wind, 1)}</td>
            <td class="num">${fmtNum(s.battery, 1)}</td>
            <td class="num">${fmtNum(s.diesel, 1)}</td>
            <td class="num"><strong>$${fmtNum(s.lcoe, 4)}</strong>${lcoeBadge}</td>
            <td class="num">${fmtUSD(s.npc)}</td>
            <td class="num">${fmtUSD(s.capex)}</td>
            <td class="num">${fmtNum(s.rf, 1)}%${rfBadge}</td>
            <td class="num">${fmtNum(s.lolp, 2)}%</td>
            <td class="num">${fmtNum(s.co2_avoided, 1)}</td>
            <td class="num"><button class="btn btn-danger-ghost" data-del-id="${s.id}" title="Delete">✕</button></td>
          </tr>
        `;
      })
      .join("");

    tbody.querySelectorAll("[data-del-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.scenarios = state.scenarios.filter((x) => x.id !== btn.dataset.delId);
        persistScenarios();
        renderScenarios();
      });
    });

    renderScenarioCharts();
  }

  function renderScenarioCharts() {
    if (!state.scenarios.length) return;
    const c = getThemeColors();
    const tickFont = chartTickFont();
    const tooltipCfg = chartTooltipStyle(c);
    const labels = state.scenarios.map((s) => s.name);

    if (hasChartJs("chart-cmp-lcoe")) {
      destroyChart("cmpLcoe");
      state.charts.cmpLcoe = new Chart($("#chart-cmp-lcoe").getContext("2d"), {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "LCOE ($/kWh)", data: state.scenarios.map((s) => s.lcoe), backgroundColor: c.pv, borderRadius: 1, yAxisID: "y" },
            { label: "Renewable Fraction (%)", data: state.scenarios.map((s) => s.rf), backgroundColor: c.positive, borderRadius: 1, yAxisID: "y1" },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: c.text, boxWidth: 10, font: tickFont } },
            tooltip: tooltipCfg,
          },
          scales: {
            x: { ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
            y: { beginAtZero: true, position: "left", title: { display: true, text: "$/kWh", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
            y1: { beginAtZero: true, max: 100, position: "right", title: { display: true, text: "RF (%)", color: c.positive, font: tickFont }, ticks: { color: c.positive, font: tickFont }, grid: { drawOnChartArea: false } },
          },
        },
      });
    }

    if (hasChartJs("chart-cmp-npc")) {
      destroyChart("cmpNpc");
      state.charts.cmpNpc = new Chart($("#chart-cmp-npc").getContext("2d"), {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "Net Present Cost ($k)", data: state.scenarios.map((s) => Number((s.npc / 1000).toFixed(1))), backgroundColor: c.secondary, borderRadius: 1 },
            { label: "Initial CAPEX ($k)", data: state.scenarios.map((s) => Number((s.capex / 1000).toFixed(1))), backgroundColor: c.pv, borderRadius: 1 },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: c.text, boxWidth: 10, font: tickFont } },
            tooltip: tooltipCfg,
          },
          scales: {
            x: { ticks: { color: c.muted, font: tickFont }, grid: { display: false } },
            y: { beginAtZero: true, title: { display: true, text: "$k USD", color: c.muted, font: tickFont }, ticks: { color: c.muted, font: tickFont }, grid: { color: c.grid } },
          },
        },
      });
    }
  }

  function exportScenariosCsv() {
    if (!state.scenarios.length) return;
    const headers = ["Scenario", "Site", "PV_kWp", "Wind_kW", "BESS_kWh", "Diesel_kW", "LCOE_USD_kWh", "NPC_USD", "CAPEX_USD", "RF_pct", "LOLP_pct", "CO2_Avoided_t_yr"];
    const rows = state.scenarios.map((s) => [
      `"${s.name.replace(/"/g, '""')}"`,
      `"${s.site.replace(/"/g, '""')}"`,
      s.pv.toFixed(2), s.wind.toFixed(2), s.battery.toFixed(2), s.diesel.toFixed(2),
      s.lcoe.toFixed(4), s.npc.toFixed(2), s.capex.toFixed(2), s.rf.toFixed(2), s.lolp.toFixed(3), s.co2_avoided.toFixed(2),
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "HRES_Scenarios_Comparison.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  // ------------------------------------------------------------------------
  // 14. Event Wiring & Bootstrap
  // ------------------------------------------------------------------------
  function bindEvents() {
    // Top tabs
    $$(".nav-tab").forEach((btn) => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));
    $("#btn-goto-optimize").addEventListener("click", () => switchTab("optimize"));

    // Language & Theme
    $$(".lang-btn").forEach((btn) => btn.addEventListener("click", () => applyLanguage(btn.dataset.lang)));
    $("#theme-toggle-btn").addEventListener("click", () => applyTheme(state.theme === "dark" ? "light" : "dark"));

    // Map layer switcher
    $$(".map-layer-btn").forEach((btn) => btn.addEventListener("click", () => setMapLayer(btn.dataset.layer)));

    // Quick-jump cities
    $$("#city-pills .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#city-pills .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        const lat = parseFloat(btn.dataset.lat);
        const lon = parseFloat(btn.dataset.lon);
        $("#input-lat").value = lat;
        $("#input-lon").value = lon;
        $("#input-site-name").value = btn.dataset.name;
        updateMapMarker(lat, lon, true);
        clearUploadedWeather(false);
        fetchPreview();
      });
    });

    // Coordinate & weather inputs
    ["#input-lat", "#input-lon", "#input-year", "#select-weather-source"].forEach((id) => {
      $(id).addEventListener("change", () => {
        const lat = parseFloat($("#input-lat").value) || 0;
        const lon = parseFloat($("#input-lon").value) || 0;
        updateMapMarker(lat, lon, true);
        fetchPreview();
      });
    });
    $("#btn-refresh-weather").addEventListener("click", fetchPreview);

    // Custom Weather Drag & Drop Upload
    const dz = $("#weather-dropzone");
    const fileInput = $("#weather-file-input");
    dz.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => handleWeatherFileUpload(e.target.files[0]));
    dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("dragover"); });
    dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) handleWeatherFileUpload(e.dataTransfer.files[0]);
    });
    $("#btn-clear-upload").addEventListener("click", () => clearUploadedWeather(true));

    // Community Presets & Sliders
    $$("#community-presets .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#community-presets .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        const p = btn.dataset.preset;
        if (p === "hamlet") {
          $("#slider-households").value = 15; $("#select-school").value = "none"; $("#select-clinic").value = "none";
        } else if (p === "village") {
          $("#slider-households").value = 60; $("#select-school").value = "medium"; $("#select-clinic").value = "small";
        } else if (p === "center") {
          $("#slider-households").value = 250; $("#select-school").value = "large"; $("#select-clinic").value = "large";
        }
        $("#val-households").textContent = $("#slider-households").value;
        schedulePreview();
      });
    });

    $("#slider-households").addEventListener("input", (e) => {
      $("#val-households").textContent = e.target.value;
      $$("#community-presets .pill").forEach((p) => p.classList.remove("active"));
      schedulePreview();
    });
    ["#select-school", "#select-clinic"].forEach((id) => {
      $(id).addEventListener("change", () => {
        $$("#community-presets .pill").forEach((p) => p.classList.remove("active"));
        schedulePreview();
      });
    });

    // Reset Cost Defaults
    $("#btn-reset-costs").addEventListener("click", () => {
      $("#cost-pv-capex").value = 1000;
      $("#cost-wind-capex").value = 1600;
      $("#cost-bat-capex").value = 300;
      $("#cost-diesel-capex").value = 400;
      $("#cost-fuel-price").value = 1.30;
      $("#cost-discount-rate").value = 8.0;
      $("#cost-lifetime").value = 25;
    });

    // Preview chart tabs
    $$("#preview-chart-tabs .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#preview-chart-tabs .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        state.previewMode = btn.dataset.preview;
        renderPreviewChart();
      });
    });

    // Component Toggles
    [
      ["#toggle-pv", "#card-toggle-pv"],
      ["#toggle-wind", "#card-toggle-wind"],
      ["#toggle-battery", "#card-toggle-battery"],
      ["#toggle-diesel", "#card-toggle-diesel"],
    ].forEach(([chk, card]) => {
      $(chk).addEventListener("change", (e) => $(card).classList.toggle("enabled", e.target.checked));
    });

    // GA Mode Presets
    $$("#ga-mode-pills .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#ga-mode-pills .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        $("#input-ga-gens").value = btn.dataset.gens;
        $("#input-ga-pop").value = btn.dataset.pop;
        $("#opt-gen-text").textContent = `0 / ${btn.dataset.gens}`;
      });
    });

    // LOLP slider
    $("#slider-lolp").addEventListener("input", (e) => {
      $("#val-lolp").textContent = `${Number(e.target.value).toFixed(1)}%`;
    });

    // Run GA & Manual Sim
    $("#btn-run-optimize").addEventListener("click", startOptimization);
    $("#btn-run-manual").addEventListener("click", () => runManualSimulation(true));

    // Week 1-52 Dispatch Slider & Seasons
    $("#slider-week").addEventListener("input", (e) => {
      state.selectedWeek = parseInt(e.target.value, 10);
      $$("#season-pills .pill").forEach((p) => p.classList.toggle("active", parseInt(p.dataset.week, 10) === state.selectedWeek));
      renderDispatchChart();
    });
    $("#btn-week-prev").addEventListener("click", () => {
      state.selectedWeek = Math.max(1, state.selectedWeek - 1);
      renderDispatchChart();
    });
    $("#btn-week-next").addEventListener("click", () => {
      state.selectedWeek = Math.min(52, state.selectedWeek + 1);
      renderDispatchChart();
    });
    $$("#season-pills .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#season-pills .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        state.selectedWeek = parseInt(btn.dataset.week, 10);
        renderDispatchChart();
      });
    });

    // Cost chart view toggle
    $$("#cost-chart-mode .pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#cost-chart-mode .pill").forEach((p) => p.classList.remove("active"));
        btn.classList.add("active");
        state.costViewMode = btn.dataset.costview;
        renderCostChart();
      });
    });

    // Results actions
    $("#btn-save-scenario").addEventListener("click", () => saveCurrentScenario());
    $("#btn-export-report").addEventListener("click", () => exportReport(false));
    $("#btn-download-report").addEventListener("click", () => exportReport(true));

    // Comparator actions
    $("#btn-gen-benchmarks").addEventListener("click", generateBenchmarks);
    $("#btn-export-csv").addEventListener("click", exportScenariosCsv);
    $("#btn-clear-scenarios").addEventListener("click", () => {
      state.scenarios = [];
      persistScenarios();
      renderScenarios();
    });
  }

  async function init() {
    bindEvents();
    applyTheme(state.theme);
    initMap();
    applyLanguage(state.lang);
    checkHealth();
    await fetchPreview();
    // Run an instant baseline simulation on startup so the Results tab is populated immediately!
    await runManualSimulation(false);
    renderScenarios();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
