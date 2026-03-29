from datetime import datetime, timedelta

# Crop NPK Demands (kg/acre)
CROPS_DATA = {
    "wheat": {"name": "Wheat (گندم)", "N": 60, "P": 30, "K": 20, "stages": ["Basal", "21 days", "Tillering", "Jointing"]},
    "rice": {"name": "Rice (چاول)", "N": 75, "P": 35, "K": 30, "stages": ["Transplant", "Tillering", "Panicle Init", "Heading"]},
    "sugarcane": {"name": "Sugarcane (گنا)", "N": 120, "P": 50, "K": 80, "stages": ["Planting", "30 days", "60 days", "90 days", "120 days"]},
    "cotton": {"name": "Cotton (کپاس)", "N": 80, "P": 40, "K": 30, "stages": ["Sowing", "Squaring", "Flowering", "Boll Dev."]},
    "maize": {"name": "Maize (مکئی)", "N": 90, "P": 45, "K": 35, "stages": ["Sowing", "V6 Stage", "Tasseling", "Silking"]},
    "potato": {"name": "Potato (آلو)", "N": 100, "P": 60, "K": 100, "stages": ["Planting", "Emergence", "Tuber Init.", "Bulking"]},
    "onion": {"name": "Onion (پیاز)", "N": 70, "P": 40, "K": 50, "stages": ["Transplant", "30 days", "Bulb Dev.", "Maturity"]},
    "tomato": {"name": "Tomato (ٹماٹر)", "N": 80, "P": 50, "K": 60, "stages": ["Transplant", "30 days", "Flowering", "Fruiting"]},
}

# NPK split fractions per growth stage
SPLITS_DATA = {
    "wheat": [{"N": 0.33, "P": 1.0, "K": 1.0, "label": "Basal (at sowing)"}, {"N": 0.33, "P": 0, "K": 0, "label": "21 days after sowing"}, {"N": 0.34, "P": 0, "K": 0, "label": "Tillering / Jointing"}],
    "rice": [{"N": 0.25, "P": 1.0, "K": 0.5, "label": "Transplanting"}, {"N": 0.35, "P": 0, "K": 0.5, "label": "Active Tillering"}, {"N": 0.25, "P": 0, "K": 0, "label": "Panicle Initiation"}, {"N": 0.15, "P": 0, "K": 0, "label": "Heading Stage"}],
    "sugarcane": [{"N": 0.2, "P": 1.0, "K": 0.3, "label": "At planting"}, {"N": 0.2, "P": 0, "K": 0.2, "label": "30 days"}, {"N": 0.2, "P": 0, "K": 0.2, "label": "60 days"}, {"N": 0.2, "P": 0, "K": 0.2, "label": "90 days"}, {"N": 0.2, "P": 0, "K": 0.1, "label": "120 days"}],
    "cotton": [{"N": 0.25, "P": 1.0, "K": 1.0, "label": "At sowing"}, {"N": 0.25, "P": 0, "K": 0, "label": "Squaring"}, {"N": 0.3, "P": 0, "K": 0, "label": "Flowering"}, {"N": 0.2, "P": 0, "K": 0, "label": "Boll development"}],
}

DEFAULT_STAGE_OFFSETS = {
    "wheat": [0, 21, 45],
    "rice": [0, 21, 45, 70],
    "sugarcane": [0, 30, 60, 90, 120],
    "cotton": [0, 30, 55, 75],
    "maize": [0, 30, 55],
    "potato": [0, 21, 45],
    "onion": [0, 30, 55],
    "tomato": [0, 30, 55],
}

def calculate_npk_formula(data):
    """
    Detailed NPK calculation based on crop, soil, pH, texture, and organic matter.
    """
    crop = data.get("crop_type", "wheat").lower()
    acres = float(data.get("field_area", 1))
    soil_n = float(data.get("nitrogen", 20))
    soil_p = float(data.get("phosphorus", 8))
    soil_k = float(data.get("potassium", 120))
    ph = float(data.get("ph", 7.2))
    texture = data.get("soil_texture", "loam")
    prev_crop = data.get("prev_crop", "none")
    organic_matter = data.get("organic_matter", "none")

    crop_info = CROPS_DATA.get(crop, CROPS_DATA["wheat"])
    
    # Texture Adjustment (Sandy soil loses more N)
    tex_factor = 0.85 if texture == "sandy" else 1.05 if texture == "clay" else 1.0
    
    # pH Adjustment (Nutrient availability)
    ph_f = {"N": 1.0, "P": 1.0, "K": 1.0}
    if ph < 5.5: ph_f = {"N": 0.85, "P": 0.65, "K": 0.9}
    elif ph < 6.0: ph_f = {"N": 0.92, "P": 0.80, "K": 0.95}
    elif ph > 8.5: ph_f = {"N": 0.88, "P": 0.60, "K": 0.85}
    elif ph > 7.5: ph_f = {"N": 0.93, "P": 0.75, "K": 0.92}

    # Bonus from previous crop
    bonus = {"N": 0, "P": 0, "K": 0}
    if prev_crop == "legume": bonus = {"N": 15, "P": 3, "K": 2}
    elif prev_crop == "rice": bonus = {"N": 5, "P": 1, "K": 5}

    # Bonus from organic matter (Feature 6: ISFM integration)
    # Average nutrients in 1 ton of organic source (approximate credits in kg/acre)
    org_credits = {"N": 0, "P": 0, "K": 0}
    if organic_matter == "fym_light": 
        org_credits = {"N": 8, "P": 4, "K": 8} # 2 tons of FYM
    elif organic_matter == "fym_heavy": 
        org_credits = {"N": 20, "P": 10, "K": 20} # 5 tons of FYM
    elif organic_matter == "compost": 
        org_credits = {"N": 12, "P": 6, "K": 10}
    elif organic_matter == "green_manure": 
        org_credits = {"N": 25, "P": 5, "K": 10} # Leguminous green manure

    # Efficiency adjusted available soil nutrients
    avail_n = soil_n * 0.25
    avail_p = soil_p * 0.20
    avail_k = soil_k * 0.05

    # Net Requirements per acre (Subtracting Soil, Bonus, and ISFM credits)
    net_n = max(0, (crop_info["N"] * tex_factor / ph_f["N"]) - avail_n - bonus["N"] - org_credits["N"])
    net_p = max(0, (crop_info["P"] * tex_factor / ph_f["P"]) - avail_p - bonus["P"] - org_credits["P"])
    net_k = max(0, (crop_info["K"] * tex_factor / ph_f["K"]) - avail_k - bonus["K"] - org_credits["K"])

    # Total for field
    total_n, total_p, total_k = net_n * acres, net_p * acres, net_k * acres

    # Map to standard fertilizers
    dap_kg = round(total_p / 0.46, 1)
    n_from_dap = dap_kg * 0.18
    urea_kg = round(max(0, total_n - n_from_dap) / 0.46, 1)
    sop_kg = round(total_k / 0.50, 1)

    return {
        "crop": crop_info["name"],
        "acres": acres,
        "nutrients": {
            "N": round(total_n, 1),
            "P": round(total_p, 1),
            "K": round(total_k, 1),
            "per_acre": {"N": round(net_n, 1), "P": round(net_p, 1), "K": round(net_k, 1)}
        },
        "fertilizers": {
            "urea": urea_kg,
            "dap": dap_kg,
            "sop": sop_kg
        },
        "ph_status": get_ph_advice(ph),
        "texture_warning": "Leaching risk in sandy soil. Apply N in 4 splits." if texture == "sandy" else None
    }

def get_ph_advice(ph):
    if ph < 5.5: return {"type": "danger", "message": "Very acidic. Apply Agricultural Lime (200kg/ac)."}
    if ph < 6.5: return {"type": "warning", "message": "Acidic. Phosphorus availability low."}
    if ph <= 7.5: return {"type": "success", "message": "Ideal pH. Nutrients fully available."}
    if ph <= 8.5: return {"type": "warning", "message": "Alkaline. Apply Gypsum (75kg/ac). Use CAN instead of Urea."}
    return {"type": "danger", "message": "Highly alkaline! Apply Gypsum (150kg/ac) + Sulfur."}

def optimize_budget_logic(data):
    """
    Allocates budget to fertilizers maximizing Net Profit (Feature 7).
    Fulfillment of Feature 4: Budget-based formulation.
    """
    budget = float(data.get("budget", 10000))
    crop_selling_price = float(data.get("crop_price_per_40kg", 4200)) / 40 # Price per kg
    
    # Market Prices (Feature 4)
    prices = {
        "urea": 3400, "dap": 9800, "sop": 6500, "can": 2800, 
        "ssp": 2200, "np": 5500, "tsp": 8500
    }
    if data.get("market_prices"):
        prices.update(data.get("market_prices"))

    # Requirements (kg/ac N-P-K)
    needs = data.get("requirements", {"N": 60, "P": 30, "K": 20})
    
    # 1. Evaluate P-Optimization (DAP vs SSP vs TSP vs NP)
    # Price per kg of Phosphorus (P)
    p_options = [
        {"n": "DAP", "c": (prices["dap"]/50)/0.46, "v": 0.46, "n_val": 0.18},
        {"n": "SSP", "c": (prices["ssp"]/50)/0.18, "v": 0.18, "n_val": 0},
        {"n": "TSP", "c": (prices["tsp"]/50)/0.46, "v": 0.46, "n_val": 0},
        {"n": "Nitrophos (NP)", "c": (prices["np"]/50)/0.20, "v": 0.20, "n_val": 0.22}
    ]
    best_p = min(p_options, key=lambda x: x["c"])

    # 2. Evaluate N-Optimization (Urea vs CAN)
    n_options = [
        {"n": "Urea", "c": (prices["urea"]/50)/0.46, "v": 0.46},
        {"n": "CAN", "c": (prices["can"]/50)/0.26, "v": 0.26}
    ]
    best_n_source = min(n_options, key=lambda x: x["c"])

    # 3. K-Optimization (Standard SOP/Potash)
    cost_k = (prices["sop"] / 50) / 0.50

    total_ideal_cost = (needs["N"] * best_n_source["c"]) + (needs["P"] * best_p["c"]) + (needs["K"] * cost_k)
    
    # ROI Logic (Feature 7: Profit Maximization)
    # Yield response is typically logarithmic. We simulate the yield gain ratio.
    ratio = min(1.0, budget / total_ideal_cost)
    
    # If using less fertilizer is actually more profitable due to high cost
    # We cap the ratio if the marginal cost exceeds marginal gain
    theoretical_max_yield_gain = 400 # kg/acre increase
    if total_ideal_cost > (theoretical_max_yield_gain * crop_selling_price * 0.8):
        # High cost environment - recommend 15% less for safety
        ratio = min(ratio, 0.85)

    final_n, final_p, final_k = needs["N"] * ratio, needs["P"] * ratio, needs["K"] * ratio

    # Construct final allocation list
    plan_fert = []
    # P-Source first
    p_qty = final_p / best_p["v"]
    plan_fert.append({"name": best_p["n"], "qty": round(p_qty, 1), "cost": round(p_qty * (prices[best_p['n'].lower().split(' ')[0]]/50))})
    
    # N-Source (Subtract N already provided by P-source like DAP or NP)
    n_provided = p_qty * best_p["n_val"]
    n_needed = max(0, final_n - n_provided)
    n_qty = n_needed / best_n_source["v"]
    plan_fert.append({"name": best_n_source["n"], "qty": round(n_qty, 1), "cost": round(n_qty * (prices[best_n_source['n'].lower()]/50))})
    
    # K-Source
    k_qty = final_k / 0.50
    plan_fert.append({"name": "SOP (Potash)", "qty": round(k_qty, 1), "cost": round(k_qty * (prices["sop"]/50))})

    actual_cost = sum(f["cost"] for f in plan_fert)
    yield_gain = theoretical_max_yield_gain * (1 - (1 - ratio)**2) # Diminishing returns formula
    revenue = yield_gain * crop_selling_price
    profit = revenue - actual_cost

    return {
        "ratio": round(ratio * 100, 1),
        "plan": {
            "N": round(final_n, 1), "P": round(final_p, 1), "K": round(final_k, 1),
            "fertilizers": plan_fert
        },
        "financials": {
            "total_cost": round(actual_cost),
            "roi": round((profit / actual_cost * 100) if actual_cost > 0 else 0),
            "profit": round(profit)
        }
    }

def generate_schedule_logic(data):
    """
    Generates split application dates and amounts.
    """
    crop = data.get("crop_type", "wheat").lower()
    total_n = float(data.get("total_n", 60))
    total_p = float(data.get("total_p", 30))
    total_k = float(data.get("total_k", 20))
    sow_date_str = data.get("sow_date", datetime.now().strftime("%Y-%m-%d"))
    
    try:
        sow_date = datetime.strptime(sow_date_str, "%Y-%m-%d")
    except:
        sow_date = datetime.now()

    splits = SPLITS_DATA.get(crop, SPLITS_DATA["wheat"])
    offsets = DEFAULT_STAGE_OFFSETS.get(crop, [0, 21, 45])

    schedule = []
    for i, s in enumerate(splits):
        if i >= len(offsets): break
        date = sow_date + timedelta(days=offsets[i])
        n_amt = round(total_n * s["N"], 1)
        p_amt = round(total_p * s.get("P", 0), 1)
        k_amt = round(total_k * s.get("K", 0), 1)

        # Basic fertilizer suggestion
        fert_sug = []
        if p_amt > 0: fert_sug.append(f"DAP {round(p_amt/0.46,1)}kg")
        if n_amt > 0: 
            # Substract N coming from DAP
            rem_n = max(0, n_amt - (p_amt*0.18/0.46 if p_amt > 0 else 0))
            if rem_n > 0: fert_sug.append(f"Urea {round(rem_n/0.46,1)}kg")
        if k_amt > 0: fert_sug.append(f"SOP {round(k_amt/0.50,1)}kg")

        schedule.append({
            "stage": s["label"],
            "date": date.strftime("%d %b, %Y"),
            "N": n_amt, "P": p_amt, "K": k_amt,
            "suggestion": " + ".join(fert_sug) or "No application"
        })

    return schedule
