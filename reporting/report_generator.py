# -*- coding: utf-8 -*-
"""
Bankable Engineering & Financial Report Generator for HRES Optimizer.

Produces a 100% offline, self-contained, print-ready A4 HTML engineering report
with embedded high-DPI Matplotlib charts (base64 PNG) ready for one-click
browser printing (Ctrl+P -> Save as PDF).
"""

import os
import io
import html
import math
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

from optimization.financials import DEFAULT_COST_PARAMS

# IPCC diesel combustion factor (kg CO2 per liter of diesel burned)
DIESEL_CO2_KG_PER_LITER = 2.68
# Typical rural off-grid diesel-only benchmark specific fuel consumption (L/kWh)
BASELINE_DIESEL_L_PER_KWH = 0.32


REPORT_STRINGS: Dict[str, Dict[str, Any]] = {
    "en": {
        "dir": "ltr",
        "doc_title": "HRES Microgrid Engineering & Financial Report",
        "subtitle": "Hybrid Renewable Energy System — 8,760-Hour Techno-Economic Sizing Study",
        "print_btn": "Print / Save as PDF (Ctrl+P)",
        "generated_on": "Generated on",
        "site_location": "Site Location",
        "coordinates": "Coordinates",
        "sim_year": "Meteorological Year",
        "opt_engine": "Optimization Engine",
        "exec_summary": "1. Executive Summary",
        "sizing_arch": "Optimal System Architecture",
        "pv_label": "Solar PV",
        "wind_label": "Wind Turbine",
        "bat_label": "Battery Storage (BESS)",
        "diesel_label": "Backup Diesel Genset",
        "lcoe_label": "LCOE",
        "npc_label": "Net Present Cost (NPC)",
        "capex_label": "Initial CAPEX",
        "opex_label": "Annual OPEX (O&M + Fuel)",
        "rf_label": "Renewable Fraction",
        "lolp_label": "Reliability / LOLP",
        "fuel_label": "Annual Diesel Fuel",
        "co2_label": "Annual CO₂ Avoided",
        "lifetime_co2_note": "Lifetime CO₂ Avoided",
        "soh_label": "Battery SOH (Year 1)",
        "shortage_hours": "Shortage Hours",
        "sec_charts": "2. Technical Performance & Dispatch Visualizations",
        "chart_monthly_title": "Monthly Energy Generation Mix vs. Community Demand",
        "chart_monthly_sub": "Aggregated 8,760-hour simulation totals by energy source (MWh/month)",
        "chart_dispatch_title": "Representative Week — Hourly Power Dispatch & Battery SOC",
        "chart_dispatch_sub": "168-hour chronological EMS dispatch showing renewable supply, load, diesel backup, and battery state of charge",
        "chart_cost_title": "Lifecycle Cost Breakdown (NPC) & Initial CAPEX Allocation",
        "chart_cost_sub": "Discounted cash flows over project lifetime vs. upfront equipment investment",
        "sec_tables": "3. Engineering & Financial Breakdown",
        "tbl_arch_title": "Component Sizing & Investment Summary",
        "col_component": "Component",
        "col_capacity": "Optimal Size",
        "col_unit_capex": "Unit CAPEX",
        "col_capex": "Initial CAPEX ($)",
        "col_lifetime": "Est. Lifetime",
        "col_replacements": "Replacements",
        "tbl_energy_title": "Annual Energy Balance & Environmental KPIs",
        "col_metric": "Parameter",
        "col_value": "Value",
        "col_notes": "Engineering Notes",
        "m_annual_demand": "Total Annual Electricity Demand",
        "m_served_load": "Total Energy Served",
        "m_pv_gen": "Solar PV Annual Generation",
        "m_wind_gen": "Wind Annual Generation",
        "m_diesel_gen": "Diesel Annual Generation",
        "m_curtailed": "Excess / Curtailed Energy",
        "m_unmet": "Unmet Load",
        "m_lolp": "Loss of Load Probability (LOLP)",
        "m_rf": "Renewable Energy Fraction",
        "m_diesel_hrs": "Diesel Operating Hours",
        "m_fuel_cons": "Annual Diesel Fuel Consumption",
        "m_bat_soh": "End-of-Year-1 Battery SOH",
        "m_co2_actual": "Annual Hybrid CO₂ Emissions",
        "m_co2_avoided": "Annual CO₂ Avoided (vs. 100% Diesel)",
        "tbl_fin_title": "Discounted Cash-Flow Summary (NPC)",
        "f_capex": "Initial Capital Cost (CAPEX)",
        "f_fixed_om": "Discounted Fixed O&M",
        "f_fuel": "Discounted Fuel Cost",
        "f_repl": "Discounted Replacements",
        "f_salvage": "Discounted Salvage Credit",
        "f_npc": "Total Net Present Cost (NPC)",
        "f_ann_cost": "Equivalent Annualized Cost",
        "f_lcoe": "Levelized Cost of Energy (LCOE)",
        "sec_method": "4. Methodology & Key Modeling Assumptions",
        "method_items": [
            ("Hourly Physics (8,760 h)", "Chronological 1-hour time-step simulation driven by NASA POWER meteorological data (GHI, 2m temperature, 10m wind speed) with scientific synthetic fallback for offline reliability."),
            ("PV & Wind Models", "Solar PV incorporates NOCT cell thermal derating (α = -0.4%/°C, derating factor ~0.80–0.82). Wind uses power-law hub-height shear correction (α = 0.14) and a piecewise cubic turbine power curve."),
            ("BESS Aging & EMS Dispatch", "Load-following Energy Management System prioritizes direct renewables, charges/discharges batteries within C-rate and SOC bounds (20%–100%), and tracks cyclic throughput State-of-Health (SOH) capacity fade."),
            ("Diesel Backup Constraints", "Linear Willans fuel consumption model (F₀ = 0.08 L/h/kW_rated, F₁ = 0.25 L/kWh) with a 30% minimum loading rule to prevent engine wet-stacking; excess minimum-load output charges the battery."),
            ("Financial & CO₂ Framework", "Net Present Cost (NPC) and Levelized Cost of Energy (LCOE) computed via Capital Recovery Factor (CRF) over project lifetime ({years} yrs, discount rate {dr:.1f}%). CO₂ emissions use the IPCC diesel factor (2.68 kg CO₂/L) compared against a 100% diesel mini-grid baseline (0.32 L/kWh)."),
            ("Genetic Algorithm Sizing", "Multi-variable optimization searches PV, Wind, Battery, and Diesel capacities simultaneously to minimize LCOE subject to the target reliability constraint (LOLP).")
        ],
        "footer_left": "Generated by HRES Optimizer — Rural Microgrid Techno-Economic Design Suite",
        "footer_right": "100% Offline Self-Contained Engineering Report",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "y_mwh": "Energy (MWh)",
        "y_kw": "Power (kW)",
        "y_soc": "Battery SOC (%)",
        "x_hours": "Hours (Representative Week)",
        "lbl_load": "Load Demand",
        "lbl_pv": "Solar PV",
        "lbl_wind": "Wind",
        "lbl_diesel": "Diesel",
        "lbl_soc": "Battery SOC",
        "lbl_min_soc": "Min SOC (20%)",
        "cost_cats": ["CAPEX", "Fixed\nO&M", "Fuel", "Replace-\nment", "Salvage\nCredit"],
        "cost_y": "Present Value ($ USD)",
        "cost_left_title": "Discounted NPC Breakdown ($)",
        "cost_right_title": "Initial CAPEX by Technology",
        "no_capex": "No CAPEX data",
        "yrs": "yrs",
        "liters_yr": "L/yr",
        "hrs_yr": "h/yr",
        "tco2_yr": "tCO₂/yr",
        "tco2": "tCO₂",
        "not_used": "N/A",
        "note_demand": "Annual community electrical load",
        "note_served": "Reliability = {rel:.2f}%",
        "note_pv": "{pct:.1f}% of gross generation",
        "note_wind": "{pct:.1f}% of gross generation",
        "note_diesel": "{pct:.1f}% of gross generation",
        "note_curt": "Surplus renewable energy spilled when BESS is full",
        "note_unmet": "{hrs} shortage hours/year",
        "note_lolp": "Unmet energy / total annual demand",
        "note_rf": "1 - (Diesel Gen / Served Load)",
        "note_diesel_hrs": "Est. genset life: {life}",
        "note_fuel": "Fuel price: ${price:.2f}/L",
        "note_soh": "Cyclic throughput degradation after Year 1",
        "note_co2_act": "At 2.68 kg CO₂/L diesel burned",
        "note_co2_av": "vs. 100% diesel baseline (0.32 L/kWh); {life_co2:,.1f} tCO₂ over {years} yrs",
    },
    "fr": {
        "dir": "ltr",
        "doc_title": "Rapport d'Ingénierie & Financier — Micro-Réseau HRES",
        "subtitle": "Système Hybride d'Énergie Renouvelable — Étude Technico-Économique sur 8 760 Heures",
        "print_btn": "Imprimer / Enregistrer en PDF (Ctrl+P)",
        "generated_on": "Généré le",
        "site_location": "Site du Projet",
        "coordinates": "Coordonnées",
        "sim_year": "Année Météorologique",
        "opt_engine": "Moteur d'Optimisation",
        "exec_summary": "1. Synthèse Exécutive",
        "sizing_arch": "Architecture Optimale Dimensionnée",
        "pv_label": "Solaire Photovoltaïque (PV)",
        "wind_label": "Éolien",
        "bat_label": "Stockage Batterie (BESS)",
        "diesel_label": "Groupe Diesel d'Appoint",
        "lcoe_label": "LCOE (Coût Actualisé)",
        "npc_label": "Coût Net Actuel (NPC)",
        "capex_label": "Investissement Initial (CAPEX)",
        "opex_label": "OPEX Annuel (O&M + Carburant)",
        "rf_label": "Fraction Renouvelable",
        "lolp_label": "Fiabilité / LOLP",
        "fuel_label": "Carburant Diesel Annuel",
        "co2_label": "CO₂ Évité par An",
        "lifetime_co2_note": "CO₂ Évité sur la Durée de Vie",
        "soh_label": "SOH Batterie (An 1)",
        "shortage_hours": "Heures de Déficit",
        "sec_charts": "2. Performances Techniques & Dynamique de Dispatch",
        "chart_monthly_title": "Production Mensuelle d'Énergie vs. Demande Communautaire",
        "chart_monthly_sub": "Bilans mensuels agrégés issus de la simulation horaire sur 8 760 heures (MWh/mois)",
        "chart_dispatch_title": "Semaine Type — Dispatch Horaire & État de Charge Batterie (SOC)",
        "chart_dispatch_sub": "Fonctionnement chronologique sur 168 heures : renouvelables, demande, appoint diesel et SOC batterie",
        "chart_cost_title": "Décomposition des Coûts sur Cycle de Vie (NPC) & Répartition CAPEX",
        "chart_cost_sub": "Flux actualisés sur la durée de vie du projet vs. investissement initial par technologie",
        "sec_tables": "3. Détails d'Ingénierie & Analyse Financière",
        "tbl_arch_title": "Dimensionnement des Équipements & Investissements",
        "col_component": "Composant",
        "col_capacity": "Capacité Optimale",
        "col_unit_capex": "CAPEX Unitaire",
        "col_capex": "CAPEX Initial ($)",
        "col_lifetime": "Durée de Vie Est.",
        "col_replacements": "Remplacements",
        "tbl_energy_title": "Bilan Énergétique Annuel & Indicateurs Environnementaux",
        "col_metric": "Indicateur",
        "col_value": "Valeur",
        "col_notes": "Notes d'Ingénierie",
        "m_annual_demand": "Demande Électrique Annuelle Totale",
        "m_served_load": "Énergie Totale Desservie",
        "m_pv_gen": "Production Annuelle Solaire PV",
        "m_wind_gen": "Production Annuelle Éolienne",
        "m_diesel_gen": "Production Annuelle Diesel",
        "m_curtailed": "Énergie Excédentaire / Écrêtée",
        "m_unmet": "Énergie Non Desservie",
        "m_lolp": "Probabilité de Perte de Charge (LOLP)",
        "m_rf": "Fraction d'Énergie Renouvelable",
        "m_diesel_hrs": "Heures de Fonctionnement Diesel",
        "m_fuel_cons": "Consommation Annuelle de Carburant",
        "m_bat_soh": "État de Santé Batterie (Fin An 1)",
        "m_co2_actual": "Émissions Annuelles CO₂ (Hybride)",
        "m_co2_avoided": "CO₂ Évité / An (vs. 100% Diesel)",
        "tbl_fin_title": "Synthèse des Flux Actualisés (NPC)",
        "f_capex": "Coût d'Investissement Initial (CAPEX)",
        "f_fixed_om": "Maintenance Fixe Actualisée (O&M)",
        "f_fuel": "Coût Carburant Actualisé",
        "f_repl": "Remplacements Actualisés",
        "f_salvage": "Valeur Résiduelle Actualisée (Crédit)",
        "f_npc": "Coût Net Actuel Total (NPC)",
        "f_ann_cost": "Coût Annuel Équivalent",
        "f_lcoe": "Coût Actualisé de l'Énergie (LCOE)",
        "sec_method": "4. Méthodologie & Hypothèses de Modélisation",
        "method_items": [
            ("Simulation Physique Horaire (8 760 h)", "Modélisation chronologique au pas horaire alimentée par les données météorologiques NASA POWER (GHI, température à 2 m, vent à 10 m) avec générateur synthétique physique de secours hors-ligne."),
            ("Modèles Solaire PV & Éolien", "Le PV intègre la dégradation thermique NOCT (α = -0,4 %/°C, facteur de déclassement ~0,80–0,82). L'éolien applique la loi de cisaillement vertical au moyeu (α = 0,14) et une courbe de puissance cubique par morceaux."),
            ("Vieillissement Batterie & Dispatch EMS", "Le système de gestion d'énergie (EMS) priorise les renouvelables, gère la charge/décharge dans les limites de taux C et de SOC (20 %–100 %), et calcule la perte de capacité cyclique (SOH)."),
            ("Contraintes du Groupe Diesel", "Courbe linéaire de consommation Willans (F₀ = 0,08 L/h/kW_nom, F₁ = 0,25 L/kWh) avec charge minimale de 30 % pour éviter le glaçage moteur ; l'excédent éventuel recharge la batterie."),
            ("Cadre Financier & Bilan CO₂", "NPC et LCOE calculés par Facteur de Récupération du Capital (CRF) sur la durée du projet ({years} ans, taux d'actualisation {dr:.1f} %). Les émissions CO₂ utilisent le facteur GIEC (2,68 kg CO₂/L) face à un scénario de référence 100 % diesel (0,32 L/kWh)."),
            ("Optimisation par Algorithme Génétique", "Exploration multi-variables (PV, Éolien, Batterie, Diesel) minimisant le LCOE sous contrainte stricte de fiabilité (LOLP).")
        ],
        "footer_left": "Généré par HRES Optimizer — Outil d'Ingénierie Technico-Économique de Micro-Réseaux Ruraux",
        "footer_right": "Rapport d'Ingénierie Autonome 100 % Hors-Ligne",
        "months": ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"],
        "y_mwh": "Énergie (MWh)",
        "y_kw": "Puissance (kW)",
        "y_soc": "SOC Batterie (%)",
        "x_hours": "Heures (Semaine Représentative)",
        "lbl_load": "Demande (Charge)",
        "lbl_pv": "Solaire PV",
        "lbl_wind": "Éolien",
        "lbl_diesel": "Diesel",
        "lbl_soc": "SOC Batterie",
        "lbl_min_soc": "SOC Min (20%)",
        "cost_cats": ["CAPEX", "O&M\nFixe", "Carburant", "Remplace-\nment", "Valeur\nRésid."],
        "cost_y": "Valeur Actualisée ($ USD)",
        "cost_left_title": "Décomposition du NPC Actualisé ($)",
        "cost_right_title": "Répartition du CAPEX Initial",
        "no_capex": "Aucune donnée CAPEX",
        "yrs": "ans",
        "liters_yr": "L/an",
        "hrs_yr": "h/an",
        "tco2_yr": "tCO₂/an",
        "tco2": "tCO₂",
        "not_used": "N/A",
        "note_demand": "Consommation électrique annuelle de la communauté",
        "note_served": "Taux de couverture = {rel:.2f} %",
        "note_pv": "{pct:.1f} % de la production brute",
        "note_wind": "{pct:.1f} % de la production brute",
        "note_diesel": "{pct:.1f} % de la production brute",
        "note_curt": "Surplus renouvelable écrêté lorsque la batterie est pleine",
        "note_unmet": "{hrs} heures de déficit/an",
        "note_lolp": "Énergie non desservie / demande annuelle totale",
        "note_rf": "1 - (Production Diesel / Énergie Desservie)",
        "note_diesel_hrs": "Durée de vie estimée : {life}",
        "note_fuel": "Prix du carburant : {price:.2f} $/L",
        "note_soh": "Dégradation cyclique après 1 an d'exploitation",
        "note_co2_act": "Facteur GIEC : 2,68 kg CO₂/L de diesel",
        "note_co2_av": "vs. référence 100 % diesel (0,32 L/kWh) ; {life_co2:,.1f} tCO₂ sur {years} ans",
    },
    "ar": {
        "dir": "rtl",
        "doc_title": "التقرير الهندسي والمالي للشبكة الصغيرة الهجينة (HRES)",
        "subtitle": "دراسة تحجيم تقنية واقتصادية على مدار 8,760 ساعة سنوياً",
        "print_btn": "طباعة / حفظ كملف PDF (Ctrl+P)",
        "generated_on": "تاريخ التوليد",
        "site_location": "موقع المشروع",
        "coordinates": "الإحداثيات",
        "sim_year": "سنة بيانات الطقس",
        "opt_engine": "محرك التحسين",
        "exec_summary": "1. الملخص التنفيذي",
        "sizing_arch": "البنية المثلى للنظام",
        "pv_label": "الطاقة الشمسية (PV)",
        "wind_label": "طاقة الرياح",
        "bat_label": "تخزين البطاريات (BESS)",
        "diesel_label": "مولد الديزل الاحتياطي",
        "lcoe_label": "التكلفة المستوية للطاقة (LCOE)",
        "npc_label": "التكلفة الصافية الإجمالية (NPC)",
        "capex_label": "الاستثمار الأولي (CAPEX)",
        "opex_label": "التشغيل السنوي (O&M + الوقود)",
        "rf_label": "نسبة الطاقة المتجددة",
        "lolp_label": "الموثوقية / LOLP",
        "fuel_label": "الوقود السنوي",
        "co2_label": "انبعاثات CO₂ المتجنبة سنوياً",
        "lifetime_co2_note": "إجمالي CO₂ المتجنب طوال عمر المشروع",
        "soh_label": "صحة البطارية (السنة 1)",
        "shortage_hours": "ساعات العجز",
        "sec_charts": "2. الرسوم البيانية للأداء التقني والتشغيل",
        "chart_monthly_title": "الإنتاج الشهري للطاقة مقابل الطلب",
        "chart_monthly_sub": "مجموع الإنتاج الشهري من محاكاة 8,760 ساعة (ميجاواط ساعة/شهر)",
        "chart_dispatch_title": "أسبوع نموذجي — التوزيع الساعي وحالة شحن البطارية",
        "chart_dispatch_sub": "التشغيل الزمني على مدار 168 ساعة للطاقة المتجددة والحمل والديزل والبطارية",
        "chart_cost_title": "تحليل التكلفة الإجمالية (NPC) وتوزيع الاستثمار الأولي",
        "chart_cost_sub": "التدفقات النقدية المخصومة طوال عمر المشروع مقابل تكلفة المعدات الأولية",
        "sec_tables": "3. التفصيل الهندسي والمالي",
        "tbl_arch_title": "تحجيم المكونات والاستثمار الأولي",
        "col_component": "المكون",
        "col_capacity": "السعة المثلى",
        "col_unit_capex": "تكلفة الوحدة",
        "col_capex": "الاستثمار الأولي ($)",
        "col_lifetime": "العمر الافتراضي",
        "col_replacements": "مرات الاستبدال",
        "tbl_energy_title": "الميزان السنوي للطاقة والمؤشرات البيئية",
        "col_metric": "المؤشر",
        "col_value": "القيمة",
        "col_notes": "ملاحظات هندسية",
        "m_annual_demand": "إجمالي الطلب السنوي",
        "m_served_load": "إجمالي الطاقة الملبية",
        "m_pv_gen": "الإنتاج الشمسي السنوي",
        "m_wind_gen": "إنتاج الرياح السنوي",
        "m_diesel_gen": "إنتاج الديزل السنوي",
        "m_curtailed": "الطاقة الفائضة المهدورة",
        "m_unmet": "الطاقة غير الملبية",
        "m_lolp": "احتمال فقدان الحمل (LOLP)",
        "m_rf": "حصة الطاقة المتجددة",
        "m_diesel_hrs": "ساعات تشغيل الديزل",
        "m_fuel_cons": "الاستهلاك السنوي للوقود",
        "m_bat_soh": "صحة البطارية (نهاية السنة 1)",
        "m_co2_actual": "انبعاثات CO₂ السنوية (النظام الهجين)",
        "m_co2_avoided": "CO₂ المتجنب سنوياً (مقارنة بـ 100% ديزل)",
        "tbl_fin_title": "ملخص التكلفة الصافية المخصومة (NPC)",
        "f_capex": "الاستثمار الرأسمالي الأولي (CAPEX)",
        "f_fixed_om": "الصيانة الثابتة المخصومة",
        "f_fuel": "تكلفة الوقود المخصومة",
        "f_repl": "تكاليف الاستبدال المخصومة",
        "f_salvage": "القيمة المتبقية المخصومة",
        "f_npc": "التكلفة الصافية الإجمالية (NPC)",
        "f_ann_cost": "التكلفة السنوية المكافئة",
        "f_lcoe": "التكلفة المستوية للطاقة (LCOE)",
        "sec_method": "4. المنهجية والافتراضات الأساسية",
        "method_items": [
            ("محاكاة فيزيائية ساعية (8,760 ساعة)", "محاكاة زمنية بالساعة تعتمد على بيانات NASA POWER مع نموذج اصطناعي فيزيائي للعمل دون اتصال."),
            ("نماذج الشمس والرياح", "يحسب النموذج الشمسي التدهور الحراري (NOCT) ويصحح نموذج الرياح السرعة بارتفاع المحور مع منحنى قدرة تكعيبي."),
            ("تخزين البطاريات والتوزيع", "يدير نظام EMS الأولوية للطاقة المتجددة ويتتبع التدهور الدوري لسعة البطارية (SOH)."),
            ("مولد الديزل الاحتياطي", "منحنى استهلاك خطي مع حد أدنى للتشغيل بنسبة 30% لمنع تآكل المحرك."),
            ("الإطار المالي والبيئي", "حساب NPC و LCOE على مدى {years} سنة بمعدل خصم {dr:.1f}% ومعامل انبعاثات IPCC البالغ 2.68 كجم CO₂/لتر."),
            ("التحسين بالخوارزمية الجينية", "البحث المتعدد المتغيرات لتقليل LCOE ضمن حد الموثوقية المطلوب (LOLP).")
        ],
        "footer_left": "تم التوليد بواسطة HRES Optimizer — أداة تصميم الشبكات الصغيرة الريفية",
        "footer_right": "تقرير هندسي مستقل يعمل 100% دون إنترنت",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "y_mwh": "Energy (MWh)",
        "y_kw": "Power (kW)",
        "y_soc": "Battery SOC (%)",
        "x_hours": "Hours (Sample Week)",
        "lbl_load": "Load",
        "lbl_pv": "Solar PV",
        "lbl_wind": "Wind",
        "lbl_diesel": "Diesel",
        "lbl_soc": "Battery SOC",
        "lbl_min_soc": "Min SOC (20%)",
        "cost_cats": ["CAPEX", "Fixed O&M", "Fuel", "Replacement", "Salvage"],
        "cost_y": "Present Value ($ USD)",
        "cost_left_title": "Discounted NPC Breakdown ($)",
        "cost_right_title": "Initial CAPEX by Technology",
        "no_capex": "No CAPEX data",
        "yrs": "سنة",
        "liters_yr": "لتر/سنة",
        "hrs_yr": "ساعة/سنة",
        "tco2_yr": "طن CO₂/سنة",
        "tco2": "طن CO₂",
        "not_used": "غير مستخدم",
        "note_demand": "إجمالي الاستهلاك الكهربائي السنوي",
        "note_served": "الموثوقية = {rel:.2f}%",
        "note_pv": "{pct:.1f}% من الإنتاج الإجمالي",
        "note_wind": "{pct:.1f}% من الإنتاج الإجمالي",
        "note_diesel": "{pct:.1f}% من الإنتاج الإجمالي",
        "note_curt": "فائض الطاقة المتجددة عند امتلاء البطاريات",
        "note_unmet": "{hrs} ساعة عجز سنوياً",
        "note_lolp": "الطاقة غير الملبية / إجمالي الطلب",
        "note_rf": "1 - (إنتاج الديزل / الطاقة الملبية)",
        "note_diesel_hrs": "العمر المقدر للمولد: {life}",
        "note_fuel": "سعر الوقود: ${price:.2f}/لتر",
        "note_soh": "التدهور الدوري بعد السنة الأولى",
        "note_co2_act": "بمعدل 2.68 كجم CO₂ لكل لتر ديزل",
        "note_co2_av": "مقارنة بمرجع 100% ديزل؛ {life_co2:,.1f} طن CO₂ خلال {years} سنة",
    },
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any numeric input to a finite float."""
    try:
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return default
        return val
    except (TypeError, ValueError):
        return default


def _fig_to_base64_and_optional_png(
    fig: Figure,
    dpi: int = 180,
    save_png_path: Optional[str] = None
) -> str:
    """Renders a Matplotlib Figure via Agg (thread/headless safe) to base64 PNG string."""
    FigureCanvasAgg(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    png_bytes = buf.getvalue()
    buf.close()

    if save_png_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_png_path)), exist_ok=True)
        with open(save_png_path, "wb") as f:
            f.write(png_bytes)

    return base64.b64encode(png_bytes).decode("ascii")


def _ensure_datetime_index(df: pd.DataFrame, year: int = 2023) -> pd.DataFrame:
    """Ensures hourly_df has a DatetimeIndex for monthly aggregation."""
    if isinstance(df.index, pd.DatetimeIndex):
        return df
    out = df.copy()
    idx = pd.date_range(start=f"{year}-01-01 00:00:00", periods=len(out), freq="h")
    out.index = idx
    return out


def _pick_representative_week(hourly_df: pd.DataFrame, requested_day: Optional[int] = None) -> Tuple[int, int]:
    """Selects a 168-hour window (start_idx, end_idx) showcasing realistic microgrid operation."""
    n = len(hourly_df)
    if n <= 168:
        return 0, n
    if requested_day is not None:
        start = max(0, min(n - 168, (int(requested_day) - 1) * 24))
        return start, start + 168

    # Prefer a week in mid-year (around week 22 / early June) where solar/wind/load are active;
    # if diesel ever operates, try to find a week that also illustrates battery cycling + backup.
    default_start = min(n - 168, 150 * 24)
    if "diesel_output" in hourly_df.columns and float(hourly_df["diesel_output"].sum()) > 0:
        # Look for a week with moderate diesel dispatch (not extreme outage, not zero)
        weekly_diesel = [
            float(hourly_df["diesel_output"].iloc[d * 24:(d + 7) * 24].sum())
            for d in range(0, (n - 168) // 24, 7)
        ]
        nonzero_weeks = [(idx, val) for idx, val in enumerate(weekly_diesel) if val > 0]
        if nonzero_weeks:
            # Pick median diesel week for a realistic representative view
            nonzero_weeks.sort(key=lambda x: x[1])
            chosen_week = nonzero_weeks[len(nonzero_weeks) // 2][0]
            start = min(n - 168, chosen_week * 7 * 24)
            return start, start + 168

    return default_start, default_start + 168


def _build_monthly_energy_chart(
    hourly_df: pd.DataFrame,
    t: Dict[str, Any],
    save_png_path: Optional[str] = None
) -> str:
    """Chart (a): Monthly Stacked Energy Generation (PV, Wind, Diesel) vs. Monthly Load."""
    df = _ensure_datetime_index(hourly_df)
    load_col = "load" if "load" in df.columns else ("total_load" if "total_load" in df.columns else df.columns[0])

    grouped = pd.DataFrame({
        "pv": df["pv_output"].values if "pv_output" in df.columns else np.zeros(len(df)),
        "wind": df["wind_output"].values if "wind_output" in df.columns else np.zeros(len(df)),
        "diesel": df["diesel_output"].values if "diesel_output" in df.columns else np.zeros(len(df)),
        "load": df[load_col].values,
    }, index=df.index)

    monthly_mwh = grouped.groupby(grouped.index.month).sum() / 1000.0
    monthly_mwh = monthly_mwh.reindex(range(1, 13), fill_value=0.0)

    x = np.arange(12)
    months = t["months"]
    pv_vals = monthly_mwh["pv"].values
    wind_vals = monthly_mwh["wind"].values
    diesel_vals = monthly_mwh["diesel"].values
    load_vals = monthly_mwh["load"].values

    fig = Figure(figsize=(8.6, 3.7), facecolor="white")
    ax = fig.add_subplot(111)
    ax.set_facecolor("#fafbfc")

    width = 0.62
    ax.bar(x, pv_vals, width, label=t["lbl_pv"], color="#f59e0b", edgecolor="white", linewidth=0.5, zorder=3)
    ax.bar(x, wind_vals, width, bottom=pv_vals, label=t["lbl_wind"], color="#0ea5e9", edgecolor="white", linewidth=0.5, zorder=3)
    ax.bar(x, diesel_vals, width, bottom=pv_vals + wind_vals, label=t["lbl_diesel"], color="#64748b", edgecolor="white", linewidth=0.5, zorder=3)

    ax.plot(x, load_vals, color="#dc2626", marker="o", markersize=4.5, linewidth=2.2, label=t["lbl_load"], zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=9, fontweight="bold", color="#334155")
    ax.set_ylabel(t["y_mwh"], fontsize=9.5, fontweight="bold", color="#1e293b")
    ax.set_title(t["chart_monthly_title"], fontsize=11, fontweight="bold", color="#0f172a", pad=10)
    ax.grid(axis="y", linestyle="--", alpha=0.45, color="#cbd5e1", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.set_ylim(bottom=0)

    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False, fontsize=8.8)
    fig.tight_layout(rect=[0, 0.05, 1, 1])

    return _fig_to_base64_and_optional_png(fig, dpi=180, save_png_path=save_png_path)


def _build_weekly_dispatch_chart(
    hourly_df: pd.DataFrame,
    t: Dict[str, Any],
    sample_week_start_day: Optional[int] = None,
    save_png_path: Optional[str] = None
) -> str:
    """Chart (b): Sample Week (168h) Hourly Dispatch & Battery SOC Curve."""
    df = _ensure_datetime_index(hourly_df)
    load_col = "load" if "load" in df.columns else ("total_load" if "total_load" in df.columns else df.columns[0])

    start_idx, end_idx = _pick_representative_week(df, sample_week_start_day)
    sub = df.iloc[start_idx:end_idx]
    hours = np.arange(len(sub))

    fig = Figure(figsize=(8.6, 3.85), facecolor="white")
    ax1 = fig.add_subplot(111)
    ax1.set_facecolor("#fafbfc")

    if "pv_output" in sub.columns and float(sub["pv_output"].max()) > 0:
        ax1.fill_between(hours, sub["pv_output"].values, color="#f59e0b", alpha=0.22, zorder=2)
        ax1.plot(hours, sub["pv_output"].values, color="#d97706", linewidth=1.4, label=f"{t['lbl_pv']} (kW)", zorder=3)

    if "wind_output" in sub.columns and float(sub["wind_output"].max()) > 0:
        ax1.fill_between(hours, sub["wind_output"].values, color="#0ea5e9", alpha=0.16, zorder=2)
        ax1.plot(hours, sub["wind_output"].values, color="#0284c7", linewidth=1.3, label=f"{t['lbl_wind']} (kW)", zorder=3)

    if "diesel_output" in sub.columns and float(sub["diesel_output"].max()) > 0:
        ax1.fill_between(hours, sub["diesel_output"].values, color="#64748b", alpha=0.25, zorder=2)
        ax1.plot(hours, sub["diesel_output"].values, color="#475569", linewidth=1.3, label=f"{t['lbl_diesel']} (kW)", zorder=4)

    ax1.plot(hours, sub[load_col].values, color="#dc2626", linewidth=1.8, linestyle="--", label=f"{t['lbl_load']} (kW)", zorder=5)

    ax1.set_ylabel(t["y_kw"], fontsize=9.5, fontweight="bold", color="#1e293b")
    ax1.set_xlabel(t["x_hours"], fontsize=9, color="#475569")
    ax1.set_xlim(0, max(1, len(sub) - 1))
    ax1.set_ylim(bottom=0)
    ax1.grid(True, linestyle="--", alpha=0.4, color="#cbd5e1", zorder=0)
    ax1.spines["top"].set_visible(False)

    # Day ticks (every 24h)
    tick_positions = list(range(0, len(sub), 24))
    tick_labels = [sub.index[p].strftime("%b %d") for p in tick_positions]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels, fontsize=8.5, color="#334155")

    lines1, labels1 = ax1.get_legend_handles_labels()

    has_soc = "battery_soc" in sub.columns and float(sub["battery_soc"].max()) > 0
    if has_soc:
        ax2 = ax1.twinx()
        soc_pct = np.clip(sub["battery_soc"].values * 100.0, 0.0, 100.0)
        ax2.plot(hours, soc_pct, color="#16a34a", linewidth=1.7, label=f"{t['lbl_soc']} (%)", zorder=6)
        ax2.axhline(20.0, color="#16a34a", linestyle=":", linewidth=1.0, alpha=0.65, label=t["lbl_min_soc"])
        ax2.set_ylabel(t["y_soc"], fontsize=9.5, fontweight="bold", color="#15803d")
        ax2.tick_params(axis="y", colors="#15803d", labelsize=8.5)
        ax2.set_ylim(0, 108)
        ax2.spines["top"].set_visible(False)
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines1 += lines2
        labels1 += labels2

    start_str = sub.index[0].strftime("%Y-%m-%d")
    end_str = sub.index[-1].strftime("%Y-%m-%d")
    ax1.set_title(f"{t['chart_dispatch_title']} ({start_str} → {end_str})", fontsize=10.8, fontweight="bold", color="#0f172a", pad=10)
    ax1.legend(lines1, labels1, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=min(len(labels1), 3), frameon=False, fontsize=8.3)
    fig.tight_layout(rect=[0, 0.06, 1, 1])

    return _fig_to_base64_and_optional_png(fig, dpi=180, save_png_path=save_png_path)


def _build_cost_breakdown_chart(
    fin: Dict[str, Any],
    t: Dict[str, Any],
    save_png_path: Optional[str] = None
) -> str:
    """Chart (c): Dual-panel Cost Breakdown (NPC components + Initial CAPEX by technology)."""
    capex = _safe_float(fin.get("capital_cost", 0.0))
    disc_om_total = _safe_float(fin.get("discounted_om", 0.0))

    # Separate Fixed O&M and Fuel cleanly (compatible with both old & upgraded financials dicts)
    if "discounted_fixed_om" in fin and "discounted_fuel" in fin:
        disc_fixed_om = _safe_float(fin["discounted_fixed_om"])
        disc_fuel = _safe_float(fin["discounted_fuel"])
    else:
        ann_om = _safe_float(fin.get("annual_om_cost", 0.0))
        ann_fuel = _safe_float(fin.get("annual_fuel_cost", 0.0))
        if ann_om > 0:
            fuel_ratio = min(1.0, max(0.0, ann_fuel / ann_om))
            disc_fuel = disc_om_total * fuel_ratio
            disc_fixed_om = disc_om_total - disc_fuel
        else:
            disc_fuel = 0.0
            disc_fixed_om = disc_om_total

    disc_repl = _safe_float(fin.get("discounted_replacement", 0.0))
    disc_salvage = _safe_float(fin.get("discounted_salvage", 0.0))

    fig = Figure(figsize=(8.6, 3.65), facecolor="white")
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    # Left panel: NPC Cost Breakdown Bar Chart
    ax1.set_facecolor("#fafbfc")
    cats = t["cost_cats"]
    vals = [capex, disc_fixed_om, disc_fuel, disc_repl, -disc_salvage]
    colors = ["#1d4ed8", "#0d9488", "#d97706", "#7c3aed", "#16a34a"]

    bars = ax1.bar(range(len(cats)), vals, color=colors, width=0.58, edgecolor="white", linewidth=0.6, zorder=3)
    ax1.axhline(0, color="#475569", linewidth=0.8, zorder=4)
    ax1.set_xticks(range(len(cats)))
    ax1.set_xticklabels(cats, fontsize=8.2, fontweight="bold", color="#334155")
    ax1.set_ylabel(t["cost_y"], fontsize=8.8, fontweight="bold", color="#1e293b")
    ax1.set_title(t["cost_left_title"], fontsize=10, fontweight="bold", color="#0f172a", pad=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.45, color="#cbd5e1", zorder=0)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # Value labels on bars
    max_abs = max((abs(v) for v in vals), default=1.0)
    offset = max_abs * 0.035 if max_abs > 0 else 1.0
    for bar, v in zip(bars, vals):
        sign = "-" if v < 0 else ""
        av = abs(v)
        label = f"{sign}${av/1000.0:,.1f}k" if av >= 1000 else f"{sign}${av:,.0f}"
        y_pos = v + offset if v >= 0 else v - offset
        va = "bottom" if v >= 0 else "top"
        ax1.text(bar.get_x() + bar.get_width() / 2.0, y_pos, label, ha="center", va=va, fontsize=7.8, fontweight="bold", color="#1e293b")

    # Add padding to y-limits so labels don't clip
    ymin, ymax = ax1.get_ylim()
    ax1.set_ylim(ymin - max_abs * 0.14 if ymin < 0 else 0, ymax + max_abs * 0.16)

    # Right panel: Initial CAPEX Donut Chart by Technology
    pv_cap = _safe_float(fin.get("pv_capital", 0.0))
    wind_cap = _safe_float(fin.get("wind_capital", 0.0))
    bat_cap = _safe_float(fin.get("battery_capital", 0.0))
    diesel_cap = _safe_float(fin.get("diesel_capital", 0.0))

    tech_items = [
        (t["lbl_pv"], pv_cap, "#f59e0b"),
        (t["lbl_wind"], wind_cap, "#0ea5e9"),
        (t["bat_label"].split(" (")[0], bat_cap, "#10b981"),
        (t["lbl_diesel"], diesel_cap, "#64748b"),
    ]
    active = [(lbl, val, col) for lbl, val, col in tech_items if val > 0]

    ax2.set_title(t["cost_right_title"], fontsize=10, fontweight="bold", color="#0f172a", pad=10)
    if active:
        total_active = sum(val for _, val, _ in active)
        labels_p = []
        for lbl, val, _ in active:
            share = (val / total_active * 100.0) if total_active > 0 else 0.0
            if share < 6.0:
                labels_p.append(f"{lbl}\n(${val/1000.0:,.1f}k · {share:.1f}%)")
            else:
                labels_p.append(f"{lbl}\n(${val/1000.0:,.1f}k)")
        sizes_p = [val for _, val, _ in active]
        colors_p = [col for _, _, col in active]
        wedges, texts, autotexts = ax2.pie(
            sizes_p,
            labels=labels_p,
            colors=colors_p,
            autopct=lambda pct: f"{pct:.1f}%" if pct >= 6.0 else "",
            startangle=90,
            pctdistance=0.77,
            wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
            textprops=dict(fontsize=8.0, color="#1e293b")
        )
        for at in autotexts:
            at.set_color("white")
            at.set_fontweight("bold")
            at.set_fontsize(8)
        total_cap_txt = f"CAPEX\n${sum(sizes_p)/1000.0:,.1f}k"
        ax2.text(0, 0, total_cap_txt, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#0f172a")
    else:
        ax2.text(0.5, 0.5, t["no_capex"], ha="center", va="center", fontsize=10, color="#64748b")
        ax2.axis("off")

    fig.tight_layout(pad=1.4)
    return _fig_to_base64_and_optional_png(fig, dpi=180, save_png_path=save_png_path)


def generate_engineering_report(
    hourly_df: pd.DataFrame,
    results: Dict[str, Any],
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    cost_params: Optional[Dict[str, Any]] = None,
    language: str = "en",
    sample_week_start_day: Optional[int] = None,
    save_charts_dir: Optional[str] = None,
) -> str:
    """
    Generates a standalone, print-ready A4 HTML engineering & financial report
    with embedded base64 high-DPI charts (100% offline capable).

    Parameters:
        hourly_df (pd.DataFrame): 8760-hour simulation DataFrame from `run_simulation()`.
        results (Dict[str, Any]): Results dictionary containing `best_configuration`,
            `metrics`, and `financial_details`.
        output_path (str): File path where the `.html` report will be written.
        metadata (Dict[str, Any], optional): Optional project metadata:
            - project_name (str)
            - site_name (str)
            - latitude (float)
            - longitude (float)
            - year (int)
            - households (int)
            - school_preset (str)
            - clinic_preset (str)
        cost_params (Dict[str, Any], optional): Cost assumptions used (merged with defaults).
        language (str): Report language — `'en'`, `'fr'`, or `'ar'` (default `'en'`).
        sample_week_start_day (int, optional): Starting day of year (1-358) for the
            168-hour dispatch chart. Auto-selected if omitted.
        save_charts_dir (str, optional): Optional directory where standalone PNG charts
            will also be saved (useful for documentation/README assets).

    Returns:
        str: Absolute path to the generated HTML report.
    """
    if hourly_df is None or len(hourly_df) == 0:
        raise ValueError("hourly_df must be a non-empty DataFrame.")
    if not results or "best_configuration" not in results or "metrics" not in results:
        raise ValueError("results must contain 'best_configuration' and 'metrics'.")

    lang_key = language.lower() if isinstance(language, str) else "en"
    if lang_key not in REPORT_STRINGS:
        lang_key = "en"
    t = REPORT_STRINGS[lang_key]

    meta = metadata or {}
    p = {**DEFAULT_COST_PARAMS, **(cost_params or {})}

    best = results["best_configuration"]
    metrics = results["metrics"]
    fin = results.get("financial_details", {})

    # Extract capacities
    pv_kw = _safe_float(best.get("pv_capacity", 0.0))
    wind_kw = _safe_float(best.get("wind_capacity", 0.0))
    bat_kwh = _safe_float(best.get("battery_capacity", 0.0))
    diesel_kw = _safe_float(best.get("diesel_capacity", 0.0))

    # Extract energy totals directly from hourly_df for rock-solid consistency
    df = _ensure_datetime_index(hourly_df, year=int(meta.get("year", 2023)))
    load_col = "load" if "load" in df.columns else ("total_load" if "total_load" in df.columns else df.columns[0])

    total_load_kwh = _safe_float(df[load_col].sum())
    pv_gen_kwh = _safe_float(df["pv_output"].sum()) if "pv_output" in df.columns else 0.0
    wind_gen_kwh = _safe_float(df["wind_output"].sum()) if "wind_output" in df.columns else 0.0
    diesel_gen_kwh = _safe_float(df["diesel_output"].sum()) if "diesel_output" in df.columns else 0.0
    curtailed_kwh = _safe_float(df["dump_power"].sum()) if "dump_power" in df.columns else 0.0
    unmet_kwh = _safe_float(df["unmet_load"].sum()) if "unmet_load" in df.columns else _safe_float(metrics.get("unmet_load_kwh", 0.0))
    served_kwh = max(0.0, total_load_kwh - unmet_kwh)
    gross_gen_kwh = pv_gen_kwh + wind_gen_kwh + diesel_gen_kwh

    shortage_hours = int((df["unmet_load"] > 1e-3).sum()) if "unmet_load" in df.columns else 0
    diesel_hours = _safe_float(
        metrics.get("diesel_operating_hours", float((df["diesel_output"] > 1e-3).sum()) if "diesel_output" in df.columns else 0.0)
    )
    fuel_liters = _safe_float(
        metrics.get("fuel_consumption_liters", float(df["diesel_fuel"].sum()) if "diesel_fuel" in df.columns else 0.0)
    )

    lolp_frac = _safe_float(metrics.get("lolp", unmet_kwh / total_load_kwh if total_load_kwh > 0 else 0.0))
    lolp_pct = lolp_frac * 100.0
    reliability_pct = max(0.0, min(100.0, 100.0 - lolp_pct))
    rf_pct = _safe_float(metrics.get("renewable_fraction", 0.0)) * 100.0
    bat_soh_pct = _safe_float(metrics.get("battery_soh_pct", 100.0))

    # Financial figures
    lcoe = _safe_float(metrics.get("lcoe", fin.get("lcoe", 0.0)))
    npc = _safe_float(metrics.get("npc", fin.get("npc", 0.0)))
    capex = _safe_float(metrics.get("capital_cost", fin.get("capital_cost", 0.0)))
    ann_om_total = _safe_float(metrics.get("annual_om_cost", fin.get("annual_om_cost", 0.0)))
    ann_fuel_cost = _safe_float(metrics.get("annual_fuel_cost", fin.get("annual_fuel_cost", 0.0)))
    disc_om_total = _safe_float(fin.get("discounted_om", 0.0))
    if "discounted_fixed_om" in fin and "discounted_fuel" in fin:
        disc_fixed_om = _safe_float(fin["discounted_fixed_om"])
        disc_fuel = _safe_float(fin["discounted_fuel"])
    else:
        ratio = (ann_fuel_cost / ann_om_total) if ann_om_total > 0 else 0.0
        disc_fuel = disc_om_total * min(1.0, max(0.0, ratio))
        disc_fixed_om = disc_om_total - disc_fuel
    disc_repl = _safe_float(fin.get("discounted_replacement", 0.0))
    disc_salvage = _safe_float(fin.get("discounted_salvage", 0.0))
    ann_cost = _safe_float(fin.get("annualized_cost", 0.0))

    project_lifetime = int(fin.get("project_lifetime", p["project_lifetime"]))
    discount_rate_pct = _safe_float(fin.get("discount_rate", p["discount_rate"])) * 100.0

    # CO2 avoided estimation (IPCC 2.68 kg CO2/L vs 100% diesel mini-grid baseline at 0.32 L/kWh)
    actual_co2_t_yr = (fuel_liters * DIESEL_CO2_KG_PER_LITER) / 1000.0
    baseline_diesel_liters = served_kwh * BASELINE_DIESEL_L_PER_KWH
    baseline_co2_t_yr = (baseline_diesel_liters * DIESEL_CO2_KG_PER_LITER) / 1000.0
    co2_avoided_t_yr = max(0.0, baseline_co2_t_yr - actual_co2_t_yr)
    co2_avoided_lifetime_t = co2_avoided_t_yr * project_lifetime

    # Build embedded charts (and optionally export PNGs)
    monthly_png = os.path.join(save_charts_dir, "monthly_energy_balance.png") if save_charts_dir else None
    dispatch_png = os.path.join(save_charts_dir, "weekly_dispatch_soc.png") if save_charts_dir else None
    cost_png = os.path.join(save_charts_dir, "lifecycle_cost_breakdown.png") if save_charts_dir else None

    chart_monthly_b64 = _build_monthly_energy_chart(df, t, save_png_path=monthly_png)
    chart_dispatch_b64 = _build_weekly_dispatch_chart(df, t, sample_week_start_day=sample_week_start_day, save_png_path=dispatch_png)
    chart_cost_b64 = _build_cost_breakdown_chart(fin, t, save_png_path=cost_png)

    # Component lifetimes and replacement counts
    bat_life = fin.get("battery_lifetime_years", p["battery_calendar_lifetime"])
    diesel_life = fin.get("diesel_lifetime_years", float("inf"))
    bat_life_str = f"{bat_life:.1f} {t['yrs']}" if bat_kwh > 0 and math.isfinite(_safe_float(bat_life, float("inf"))) else t["not_used"]
    diesel_life_str = (
        f"{diesel_life:.1f} {t['yrs']}"
        if diesel_kw > 0 and isinstance(diesel_life, (int, float)) and math.isfinite(diesel_life)
        else (f">{project_lifetime} {t['yrs']}" if diesel_kw > 0 else t["not_used"])
    )
    bat_reps = len(fin.get("battery_replacements", [])) if bat_kwh > 0 else 0
    diesel_reps = len(fin.get("diesel_replacements", [])) if diesel_kw > 0 else 0

    pv_capex_val = _safe_float(fin.get("pv_capital", pv_kw * p["pv_capex"]))
    wind_capex_val = _safe_float(fin.get("wind_capital", wind_kw * p["wind_capex"]))
    bat_capex_val = _safe_float(fin.get("battery_capital", bat_kwh * p["battery_capex"]))
    diesel_capex_val = _safe_float(fin.get("diesel_capital", diesel_kw * p["diesel_capex"]))

    # Metadata formatting (escaped for HTML safety)
    project_name = html.escape(str(meta.get("project_name") or t["doc_title"]))
    site_name = html.escape(str(meta.get("site_name") or "Off-Grid Rural Microgrid"))
    lat = _safe_float(meta.get("latitude", 18.0735))
    lon = _safe_float(meta.get("longitude", -15.9582))
    sim_year = int(meta.get("year", df.index[0].year if len(df) > 0 else 2023))
    opt_method = html.escape(str(results.get("optimization_method", "Genetic Algorithm")))
    generated_ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    pv_pct = (pv_gen_kwh / gross_gen_kwh * 100.0) if gross_gen_kwh > 0 else 0.0
    wind_pct = (wind_gen_kwh / gross_gen_kwh * 100.0) if gross_gen_kwh > 0 else 0.0
    diesel_pct = (diesel_gen_kwh / gross_gen_kwh * 100.0) if gross_gen_kwh > 0 else 0.0

    # Render methodology bullets
    method_html_items = []
    for title_m, desc_m in t["method_items"]:
        formatted_desc = desc_m.format(years=project_lifetime, dr=discount_rate_pct)
        method_html_items.append(
            f"<li><strong>{html.escape(title_m)}:</strong> {html.escape(formatted_desc)}</li>"
        )
    methodology_list_html = "\n          ".join(method_html_items)

    # Assemble clean, modern, print-ready A4 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="{lang_key}" dir="{t['dir']}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{project_name}</title>
  <style>
    :root {{
      --navy: #0f172a;
      --slate-800: #1e293b;
      --slate-600: #475569;
      --slate-500: #64748b;
      --slate-200: #e2e8f0;
      --slate-100: #f1f5f9;
      --slate-50: #f8fafc;
      --blue: #1d4ed8;
      --emerald: #059669;
      --amber: #d97706;
      --sky: #0284c7;
      --rose: #dc2626;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: var(--slate-800);
      background: #e2e8f0;
      line-height: 1.48;
      font-size: 13px;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    .toolbar {{
      max-width: 210mm;
      margin: 14px auto 0;
      display: flex;
      justify-content: flex-end;
      padding: 0 4px;
    }}

    .print-btn {{
      background: var(--blue);
      color: #ffffff;
      border: none;
      border-radius: 6px;
      padding: 9px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(15, 23, 42, 0.18);
    }}

    .print-btn:hover {{
      background: #1e40af;
    }}

    .page {{
      max-width: 210mm;
      margin: 12px auto 28px;
      background: #ffffff;
      padding: 16mm 15mm 14mm;
      box-shadow: 0 8px 30px rgba(15, 23, 42, 0.12);
      border-radius: 4px;
    }}

    .header {{
      border-bottom: 3px solid var(--navy);
      padding-bottom: 14px;
      margin-bottom: 18px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }}

    .header-left h1 {{
      font-size: 20px;
      color: var(--navy);
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 4px;
    }}

    .header-left .subtitle {{
      font-size: 12px;
      color: var(--slate-600);
      font-weight: 500;
    }}

    .badge {{
      display: inline-block;
      margin-top: 8px;
      background: #eff6ff;
      color: var(--blue);
      border: 1px solid #bfdbfe;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .meta-box {{
      background: var(--slate-50);
      border: 1px solid var(--slate-200);
      border-radius: 6px;
      padding: 9px 12px;
      font-size: 11px;
      min-width: 215px;
    }}

    .meta-row {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 3px;
    }}

    .meta-row:last-child {{
      margin-bottom: 0;
    }}

    .meta-key {{
      color: var(--slate-500);
      font-weight: 600;
    }}

    .meta-val {{
      color: var(--navy);
      font-weight: 700;
      text-align: end;
    }}

    h2 {{
      font-size: 14.5px;
      color: var(--navy);
      font-weight: 800;
      margin: 20px 0 10px;
      padding-bottom: 5px;
      border-bottom: 1.5px solid var(--slate-200);
      letter-spacing: -0.01em;
    }}

    h3 {{
      font-size: 12.5px;
      color: var(--slate-800);
      font-weight: 700;
      margin: 12px 0 6px;
    }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 12px;
    }}

    .kpi-card {{
      background: var(--slate-50);
      border: 1px solid var(--slate-200);
      border-top: 3px solid var(--blue);
      border-radius: 6px;
      padding: 10px 11px;
    }}

    .kpi-card.amber {{ border-top-color: var(--amber); }}
    .kpi-card.sky {{ border-top-color: var(--sky); }}
    .kpi-card.emerald {{ border-top-color: var(--emerald); }}
    .kpi-card.slate {{ border-top-color: var(--slate-600); }}
    .kpi-card.rose {{ border-top-color: var(--rose); }}

    .kpi-label {{
      font-size: 10.5px;
      font-weight: 600;
      color: var(--slate-500);
      text-transform: uppercase;
      letter-spacing: 0.03em;
      margin-bottom: 4px;
    }}

    .kpi-value {{
      font-size: 17px;
      font-weight: 800;
      color: var(--navy);
      line-height: 1.2;
    }}

    .kpi-sub {{
      font-size: 10.5px;
      color: var(--slate-600);
      margin-top: 3px;
    }}

    .chart-block {{
      margin: 12px 0 16px;
      border: 1px solid var(--slate-200);
      border-radius: 6px;
      padding: 10px 12px;
      background: #ffffff;
      page-break-inside: avoid;
      break-inside: avoid;
    }}

    .chart-caption {{
      font-size: 11px;
      color: var(--slate-500);
      margin-bottom: 6px;
    }}

    .chart-block img {{
      width: 100%;
      height: auto;
      display: block;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 14px;
      font-size: 11.8px;
      page-break-inside: avoid;
      break-inside: avoid;
    }}

    th {{
      background: var(--navy);
      color: #ffffff;
      font-weight: 700;
      text-align: start;
      padding: 7px 9px;
      font-size: 11px;
      letter-spacing: 0.02em;
    }}

    td {{
      padding: 6.5px 9px;
      border-bottom: 1px solid var(--slate-200);
    }}

    tr:nth-child(even) td {{
      background: var(--slate-50);
    }}

    tr.total-row td {{
      background: #eff6ff;
      font-weight: 800;
      color: var(--navy);
      border-top: 2px solid var(--navy);
      border-bottom: 2px solid var(--navy);
    }}

    .num {{
      text-align: end;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}

    .two-col {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 14px;
      align-items: start;
    }}

    .method-box {{
      background: var(--slate-50);
      border: 1px solid var(--slate-200);
      border-radius: 6px;
      padding: 12px 16px;
      page-break-inside: avoid;
      break-inside: avoid;
    }}

    .method-box ul {{
      padding-inline-start: 18px;
    }}

    .method-box li {{
      margin-bottom: 6px;
      font-size: 11.5px;
      color: var(--slate-800);
    }}

    .method-box li:last-child {{
      margin-bottom: 0;
    }}

    .footer {{
      margin-top: 20px;
      padding-top: 10px;
      border-top: 1px solid var(--slate-200);
      display: flex;
      justify-content: space-between;
      font-size: 10.5px;
      color: var(--slate-500);
    }}

    .page-break {{
      page-break-before: always;
      break-before: page;
    }}

    @page {{
      size: A4;
      margin: 12mm;
    }}

    @media print {{
      body {{
        background: #ffffff;
      }}
      .toolbar {{
        display: none !important;
      }}
      .page {{
        margin: 0;
        padding: 0;
        box-shadow: none;
        max-width: 100%;
        border-radius: 0;
      }}
    }}
  </style>
</head>
<body>
  <div class="toolbar">
    <button class="print-btn" onclick="window.print()">&#128424; {html.escape(t['print_btn'])}</button>
  </div>

  <div class="page">
    <!-- HEADER -->
    <div class="header">
      <div class="header-left">
        <h1>{project_name}</h1>
        <div class="subtitle">{html.escape(t['subtitle'])}</div>
        <span class="badge">HRES Optimizer &bull; 8,760h Physics &amp; GA Sizing</span>
      </div>
      <div class="meta-box">
        <div class="meta-row"><span class="meta-key">{html.escape(t['site_location'])}:</span><span class="meta-val">{site_name}</span></div>
        <div class="meta-row"><span class="meta-key">{html.escape(t['coordinates'])}:</span><span class="meta-val">{lat:.4f}°, {lon:.4f}°</span></div>
        <div class="meta-row"><span class="meta-key">{html.escape(t['sim_year'])}:</span><span class="meta-val">{sim_year}</span></div>
        <div class="meta-row"><span class="meta-key">{html.escape(t['opt_engine'])}:</span><span class="meta-val">{opt_method}</span></div>
        <div class="meta-row"><span class="meta-key">{html.escape(t['generated_on'])}:</span><span class="meta-val">{generated_ts}</span></div>
      </div>
    </div>

    <!-- 1. EXECUTIVE SUMMARY -->
    <h2>{html.escape(t['exec_summary'])}</h2>

    <h3>{html.escape(t['sizing_arch'])}</h3>
    <div class="kpi-grid">
      <div class="kpi-card amber">
        <div class="kpi-label">{html.escape(t['pv_label'])}</div>
        <div class="kpi-value">{pv_kw:,.1f} kWp</div>
        <div class="kpi-sub">{pv_gen_kwh/1000.0:,.1f} MWh/yr</div>
      </div>
      <div class="kpi-card sky">
        <div class="kpi-label">{html.escape(t['wind_label'])}</div>
        <div class="kpi-value">{wind_kw:,.1f} kW</div>
        <div class="kpi-sub">{wind_gen_kwh/1000.0:,.1f} MWh/yr</div>
      </div>
      <div class="kpi-card emerald">
        <div class="kpi-label">{html.escape(t['bat_label'])}</div>
        <div class="kpi-value">{bat_kwh:,.1f} kWh</div>
        <div class="kpi-sub">{html.escape(t['soh_label'])}: {bat_soh_pct:.2f}%</div>
      </div>
      <div class="kpi-card slate">
        <div class="kpi-label">{html.escape(t['diesel_label'])}</div>
        <div class="kpi-value">{diesel_kw:,.1f} kW</div>
        <div class="kpi-sub">{diesel_hours:,.0f} {html.escape(t['hrs_yr'])}</div>
      </div>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">{html.escape(t['lcoe_label'])}</div>
        <div class="kpi-value">${lcoe:.4f}/kWh</div>
        <div class="kpi-sub">{project_lifetime} {html.escape(t['yrs'])} @ {discount_rate_pct:.1f}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{html.escape(t['npc_label'])}</div>
        <div class="kpi-value">${npc:,.0f}</div>
        <div class="kpi-sub">{html.escape(t['capex_label'])}: ${capex:,.0f}</div>
      </div>
      <div class="kpi-card emerald">
        <div class="kpi-label">{html.escape(t['rf_label'])}</div>
        <div class="kpi-value">{rf_pct:.1f}%</div>
        <div class="kpi-sub">{html.escape(t['co2_label'])}: {co2_avoided_t_yr:,.1f} {html.escape(t['tco2_yr'])}</div>
      </div>
      <div class="kpi-card {'emerald' if lolp_pct <= 5.0 else 'rose'}">
        <div class="kpi-label">{html.escape(t['lolp_label'])}</div>
        <div class="kpi-value">{reliability_pct:.2f}%</div>
        <div class="kpi-sub">LOLP: {lolp_pct:.3f}% ({shortage_hours} h)</div>
      </div>
    </div>

    <!-- 2. CHARTS -->
    <h2>{html.escape(t['sec_charts'])}</h2>

    <div class="chart-block">
      <div class="chart-caption">{html.escape(t['chart_monthly_sub'])}</div>
      <img src="data:image/png;base64,{chart_monthly_b64}" alt="Monthly Energy Generation vs Load" />
    </div>

    <div class="chart-block">
      <div class="chart-caption">{html.escape(t['chart_dispatch_sub'])}</div>
      <img src="data:image/png;base64,{chart_dispatch_b64}" alt="Sample Week Hourly Dispatch and Battery SOC" />
    </div>

    <div class="chart-block">
      <div class="chart-caption">{html.escape(t['chart_cost_sub'])}</div>
      <img src="data:image/png;base64,{chart_cost_b64}" alt="Lifecycle Cost Breakdown" />
    </div>

    <!-- 3. DETAILED TABLES -->
    <h2>{html.escape(t['sec_tables'])}</h2>

    <h3>{html.escape(t['tbl_arch_title'])}</h3>
    <table>
      <thead>
        <tr>
          <th>{html.escape(t['col_component'])}</th>
          <th class="num">{html.escape(t['col_capacity'])}</th>
          <th class="num">{html.escape(t['col_unit_capex'])}</th>
          <th class="num">{html.escape(t['col_capex'])}</th>
          <th class="num">{html.escape(t['col_lifetime'])}</th>
          <th class="num">{html.escape(t['col_replacements'])}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>{html.escape(t['pv_label'])}</strong></td>
          <td class="num">{pv_kw:,.2f} kWp</td>
          <td class="num">${_safe_float(p['pv_capex']):,.0f}/kW</td>
          <td class="num">${pv_capex_val:,.2f}</td>
          <td class="num">{int(p['pv_lifetime'])} {html.escape(t['yrs'])}</td>
          <td class="num">0</td>
        </tr>
        <tr>
          <td><strong>{html.escape(t['wind_label'])}</strong></td>
          <td class="num">{wind_kw:,.2f} kW</td>
          <td class="num">${_safe_float(p['wind_capex']):,.0f}/kW</td>
          <td class="num">${wind_capex_val:,.2f}</td>
          <td class="num">{int(p['wind_lifetime'])} {html.escape(t['yrs'])}</td>
          <td class="num">{1 if (wind_kw > 0 and p['wind_lifetime'] < project_lifetime) else 0}</td>
        </tr>
        <tr>
          <td><strong>{html.escape(t['bat_label'])}</strong></td>
          <td class="num">{bat_kwh:,.2f} kWh</td>
          <td class="num">${_safe_float(p['battery_capex']):,.0f}/kWh</td>
          <td class="num">${bat_capex_val:,.2f}</td>
          <td class="num">{html.escape(bat_life_str)}</td>
          <td class="num">{bat_reps}</td>
        </tr>
        <tr>
          <td><strong>{html.escape(t['diesel_label'])}</strong></td>
          <td class="num">{diesel_kw:,.2f} kW</td>
          <td class="num">${_safe_float(p['diesel_capex']):,.0f}/kW</td>
          <td class="num">${diesel_capex_val:,.2f}</td>
          <td class="num">{html.escape(diesel_life_str)}</td>
          <td class="num">{diesel_reps}</td>
        </tr>
        <tr class="total-row">
          <td colspan="3">{html.escape(t['capex_label'])}</td>
          <td class="num">${capex:,.2f}</td>
          <td colspan="2"></td>
        </tr>
      </tbody>
    </table>

    <div class="two-col">
      <div>
        <h3>{html.escape(t['tbl_energy_title'])}</h3>
        <table>
          <thead>
            <tr>
              <th>{html.escape(t['col_metric'])}</th>
              <th class="num">{html.escape(t['col_value'])}</th>
              <th>{html.escape(t['col_notes'])}</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>{html.escape(t['m_annual_demand'])}</td><td class="num">{total_load_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_demand'])}</td></tr>
            <tr><td>{html.escape(t['m_served_load'])}</td><td class="num">{served_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_served'].format(rel=reliability_pct))}</td></tr>
            <tr><td>{html.escape(t['m_pv_gen'])}</td><td class="num">{pv_gen_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_pv'].format(pct=pv_pct))}</td></tr>
            <tr><td>{html.escape(t['m_wind_gen'])}</td><td class="num">{wind_gen_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_wind'].format(pct=wind_pct))}</td></tr>
            <tr><td>{html.escape(t['m_diesel_gen'])}</td><td class="num">{diesel_gen_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_diesel'].format(pct=diesel_pct))}</td></tr>
            <tr><td>{html.escape(t['m_curtailed'])}</td><td class="num">{curtailed_kwh/1000.0:,.2f} MWh</td><td>{html.escape(t['note_curt'])}</td></tr>
            <tr><td>{html.escape(t['m_unmet'])}</td><td class="num">{unmet_kwh:,.1f} kWh</td><td>{html.escape(t['note_unmet'].format(hrs=shortage_hours))}</td></tr>
            <tr><td>{html.escape(t['m_lolp'])}</td><td class="num">{lolp_pct:.3f}%</td><td>{html.escape(t['note_lolp'])}</td></tr>
            <tr><td>{html.escape(t['m_rf'])}</td><td class="num">{rf_pct:.1f}%</td><td>{html.escape(t['note_rf'])}</td></tr>
            <tr><td>{html.escape(t['m_diesel_hrs'])}</td><td class="num">{diesel_hours:,.0f} {html.escape(t['hrs_yr'])}</td><td>{html.escape(t['note_diesel_hrs'].format(life=diesel_life_str))}</td></tr>
            <tr><td>{html.escape(t['m_fuel_cons'])}</td><td class="num">{fuel_liters:,.1f} {html.escape(t['liters_yr'])}</td><td>{html.escape(t['note_fuel'].format(price=_safe_float(p['diesel_fuel_price'])))}</td></tr>
            <tr><td>{html.escape(t['m_bat_soh'])}</td><td class="num">{bat_soh_pct:.2f}%</td><td>{html.escape(t['note_soh'])}</td></tr>
            <tr><td>{html.escape(t['m_co2_actual'])}</td><td class="num">{actual_co2_t_yr:,.2f} {html.escape(t['tco2_yr'])}</td><td>{html.escape(t['note_co2_act'])}</td></tr>
            <tr class="total-row"><td>{html.escape(t['m_co2_avoided'])}</td><td class="num">{co2_avoided_t_yr:,.2f} {html.escape(t['tco2_yr'])}</td><td>{html.escape(t['note_co2_av'].format(life_co2=co2_avoided_lifetime_t, years=project_lifetime))}</td></tr>
          </tbody>
        </table>
      </div>

      <div>
        <h3>{html.escape(t['tbl_fin_title'])}</h3>
        <table>
          <thead>
            <tr>
              <th>{html.escape(t['col_metric'])}</th>
              <th class="num">{html.escape(t['col_value'])}</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>{html.escape(t['f_capex'])}</td><td class="num">${capex:,.2f}</td></tr>
            <tr><td>{html.escape(t['f_fixed_om'])}</td><td class="num">${disc_fixed_om:,.2f}</td></tr>
            <tr><td>{html.escape(t['f_fuel'])}</td><td class="num">${disc_fuel:,.2f}</td></tr>
            <tr><td>{html.escape(t['f_repl'])}</td><td class="num">${disc_repl:,.2f}</td></tr>
            <tr><td>{html.escape(t['f_salvage'])}</td><td class="num">-${disc_salvage:,.2f}</td></tr>
            <tr class="total-row"><td>{html.escape(t['f_npc'])}</td><td class="num">${npc:,.2f}</td></tr>
            <tr><td>{html.escape(t['opex_label'])}</td><td class="num">${ann_om_total:,.2f}/yr</td></tr>
            <tr><td>{html.escape(t['f_ann_cost'])}</td><td class="num">${ann_cost:,.2f}/yr</td></tr>
            <tr class="total-row"><td>{html.escape(t['f_lcoe'])}</td><td class="num">${lcoe:.4f}/kWh</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 4. METHODOLOGY -->
    <h2>{html.escape(t['sec_method'])}</h2>
    <div class="method-box">
      <ul>
          {methodology_list_html}
      </ul>
    </div>

    <!-- FOOTER -->
    <div class="footer">
      <span>{html.escape(t['footer_left'])}</span>
      <span>{html.escape(t['footer_right'])}</span>
    </div>
  </div>
</body>
</html>
"""

    abs_out = os.path.abspath(output_path)
    out_dir = os.path.dirname(abs_out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(abs_out, "w", encoding="utf-8") as f:
        f.write(html_content)

    return abs_out
