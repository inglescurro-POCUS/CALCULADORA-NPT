/**
 * NPT Calculator Core Logic
 * Pure functions for calculating nutritional requirements.
 */

const NPT = {
    // Utility
    round: (v, d = 0) => {
        const p = Math.pow(10, d);
        return Math.round((v + Number.EPSILON) * p) / p;
    },

    clamp: (v, a, b) => Math.min(Math.max(v, a), b),

    // derived: BMI
    calcBMI: (weight, heightCm) => {
        return heightCm > 0 ? weight / Math.pow(heightCm / 100, 2) : 0;
    },

    // IBW & AdjBW
    calcIBW: (sex, heightCm) => {
        // Devine Formula
        // Male: 50 + 0.9 * (height - 152)
        // Female: 45.5 + 0.9 * (height - 152)
        const base = sex === 'H' ? 50 : 45.5;
        return base + 0.9 * (heightCm - 152);
    },

    calcAdjBW: (ibw, actualWeight) => {
        // AdjBW = IBW + 0.25 * (Actual - IBW)
        return ibw + 0.25 * (actualWeight - ibw);
    },

    getCalculationWeight: (actualWeight, adjBW, bmi) => {
        // Use Adjusted Body Weight if BMI >= 30 (Obesity)
        return bmi >= 30 ? adjBW : actualWeight;
    },

    // Core Calculations
    calculateRequirements: (params) => {
        const {
            weightCalc, // Pre-calculated weight to use (Real or Adj)
            kcalKg,
            protKg,
            startPct, // 0.0 to 1.0 (e.g. 0.8 for 80%)
            pctGluc, // % of non-protein calories
            aaPct // % concentration of AA solution (e.g. 10, 15)
        } = params;

        // Energy
        const kcalTarget = kcalKg * weightCalc;
        const kcalDay = kcalTarget * startPct;

        // Protein
        const protDay = protKg * weightCalc;
        const nitrogenDay = protDay / 6.25;
        const kcalProt = protDay * 4;

        // Non-Protein Calories
        const kcalNoProt = Math.max(kcalDay - kcalProt, 0);
        const kcalGlu = kcalNoProt * (pctGluc / 100);
        const kcalLip = kcalNoProt - kcalGlu;

        // Grams
        const gGlu = kcalGlu / 3.4;
        const gLip = kcalLip / 9;

        // Volumes
        const mlD50 = gGlu / 0.5; // Dextrose 50% = 0.5 g/mL
        const mlLip20 = gLip / 0.2; // Lipids 20% = 0.2 g/mL
        const mlAA = (protDay * 100) / aaPct; // AA Volume based on concentration

        const volTotal = mlAA + mlD50 + mlLip20; // Base volume without electrolytes/additives
        const rate = volTotal / 24;

        return {
            kcalTarget,
            kcalDay,
            protDay,
            nitrogenDay,
            gGlu,
            gLip,
            mlD50,
            mlLip20,
            mlAA,
            volTotal,
            rate
        };
    },

    // Safety Checks
    checkSafety: (results, weightCalc, condition) => {
        const { gGlu, gLip } = results;

        // Glucose Infusion Rate
        const gir_g_kg_d = weightCalc > 0 ? gGlu / weightCalc : 0;
        const gir_mg_kg_min = weightCalc > 0 ? (gGlu * 1000) / (weightCalc * 1440) : 0;

        // Lipid Load
        const lip_g_kg_d = weightCalc > 0 ? gLip / weightCalc : 0;

        return {
            glucose: {
                val: gir_g_kg_d,
                valMin: gir_mg_kg_min,
                ok: gir_g_kg_d <= 5, // Threshold 5 g/kg/d check
                msg: gir_g_kg_d > 5 ? 'Excede 5 g/kg/d. Riesgo de hiperglucemia/↑CO₂.' : 'Dentro de rangos seguros.'
            },
            lipids: {
                val: lip_g_kg_d,
                ok: lip_g_kg_d <= 1.5,
                warn: lip_g_kg_d < 0.7,
                msg: lip_g_kg_d > 1.5 ? 'Excede 1.5 g/kg/d (Sobrecarga).' :
                    (lip_g_kg_d < 0.7 ? 'Bajo aporte (<0.7 g/kg/d). Riesgo déficit AGE si se mantiene.' : 'Aporte correcto.')
            }
        };
    }
};
