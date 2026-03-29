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

    # Bonus from organic matter
    org = {"N": 0, "P": 0, "K": 0}
    if organic_matter == "fym_light": org = {"N": 10, "P": 5, "K": 8}
    elif organic_matter == "fym_heavy": org = {"N": 20, "P": 10, "K": 15}
    elif organic_matter == "compost": org = {"N": 15, "P": 7, "K": 10}
    elif organic_matter == "green_manure": org = {"N": 20, "P": 5, "K": 5}

    # Efficiency adjusted available soil nutrients
    avail_n = soil_n * 0.25
    avail_p = soil_p * 0.20
    avail_k = soil_k * 0.05

    # Net Requirements per acre
    net_n = max(0, (crop_info["N"] * tex_factor / ph_f["N"]) - avail_n - bonus["N"] - org["N"])
    net_p = max(0, (crop_info["P"] * tex_factor / ph_f["P"]) - avail_p - bonus["P"] - org["P"])
    net_k = max(0, (crop_info["K"] * tex_factor / ph_f["K"]) - avail_k - bonus["K"] - org["K"])

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
    Allocates budget to fertilizers maximizing ROI.
    """
    budget = float(data.get("budget", 10000))
    crop_selling_price = float(data.get("crop_price_per_40kg", 4200)) / 40 # Price per kg
    prices = data.get("market_prices", {
        "urea": 3400, "dap": 9800, "sop": 6500, "can": 2800, "ssp": 2200, "np": 5500
    })

    # Needs (from previous calculation or defaults)
    needs = data.get("requirements", {"N": 60, "P": 30, "K": 20}) # defaults per acre
    
    # Cheapest sources
    # N: Urea vs CAN
    cost_n_urea = (prices["urea"] / 50) / 0.46
    cost_n_can = (prices["can"] / 50) / 0.26
    best_n = {"name": "Urea", "cost": cost_n_urea, "content": 0.46} if cost_n_urea < cost_n_can else {"name": "CAN", "cost": cost_n_can, "content": 0.26}

    # P: DAP vs SSP vs NP
    cost_p_dap = (prices["dap"] / 50) / 0.46
    cost_p_ssp = (prices["ssp"] / 50) / 0.18
    costs_p = [{"n": "DAP", "c": cost_p_dap, "v": 0.46}, {"n": "SSP", "c": cost_p_ssp, "v": 0.18}]
    best_p = min(costs_p, key=lambda x: x["c"])

    cost_k = (prices["sop"] / 50) / 0.50

    total_ideal_cost = (needs["N"] * best_n["cost"]) + (needs["P"] * best_p["c"]) + (needs["K"] * cost_k)
    ratio = min(1.0, budget / total_ideal_cost)

    final_n = needs["N"] * ratio
    final_p = needs["P"] * ratio
    final_k = needs["K"] * ratio

    actual_cost = (final_n * best_n["cost"]) + (final_p * best_p["c"]) + (final_k * cost_k)
    
    # ROI (Simplified)
    yield_gain = 40 * ratio # Assume 40 maunds/acre potential gain
    revenue = yield_gain * 40 * crop_selling_price
    profit = revenue - actual_cost

    return {
        "ratio": round(ratio * 100, 1),
        "plan": {
            "N": round(final_n, 1), "P": round(final_p, 1), "K": round(final_k, 1),
            "fertilizers": [
                {"name": best_n["name"], "qty": round(final_n / best_n["content"], 1), "cost": round(final_n * best_n["cost"])},
                {"name": best_p["n"], "qty": round(final_p / best_p["v"], 1), "cost": round(final_p * best_p["c"])},
                {"name": "SOP", "qty": round(final_k / 0.50, 1), "cost": round(final_k * cost_k)}
            ]
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
