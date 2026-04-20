from flask import Flask, request, jsonify
import swisseph as swe
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta

app = Flask(__name__)
geolocator = Nominatim(user_agent="supreme_astro_engine_2026")

@app.route('/get_kundli', methods=['POST'])
def get_kundli():
    try:
        data = request.json
        dob = data.get('dob') 
        tob = data.get('tob') 
        place = data.get('place') 
        
        # 1. Location
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"status": "error", "message": "Shahar ka naam nahi mila."})
        lat, lon = location.latitude, location.longitude
        
        # 2. Perfect Time Conversion (IST to UTC Fix)
        year_str, month_str, day_str = map(int, dob.split('-'))
        hour_str, minute_str = map(int, tob.split(':'))
        
        ist_time = datetime(year_str, month_str, day_str, hour_str, minute_str)
        utc_time = ist_time - timedelta(hours=5, minutes=30)
        
        year, month, day = utc_time.year, utc_time.month, utc_time.day
        hour_utc, minute_utc = utc_time.hour, utc_time.minute
            
        # 3. Swiss Ephemeris Setup
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        jd = swe.julday(year, month, day, hour_utc + (minute_utc/60.0))
        
        # 4. Houses & Lagna
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        lagna_degree = ascmc[0]
        zodiacs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        lagna_index = int(lagna_degree / 30)
        lagna_sign = zodiacs[lagna_index]
        
        planets = {
            "Surya": swe.SUN, "Chandra": swe.MOON, 
            "Mangal": swe.MARS, "Budh": swe.MERCURY,
            "Guru": swe.JUPITER, "Shukra": swe.VENUS,
            "Shani": swe.SATURN, "Rahu": swe.TRUE_NODE
        }
        
        kundli_data = {"Lagna": lagna_sign, "Planets": {}}
        moon_absolute_degree = 0
        
        for p_name, p_code in planets.items():
            pos, _ = swe.calc_ut(jd, p_code)
            degree = pos[0]
            
            if p_code == swe.MOON:
                moon_absolute_degree = degree # Dasha ke liye save kiya
                
            sign_index = int(degree / 30)
            sign = zodiacs[sign_index]
            house = ((sign_index - lagna_index + 12) % 12) + 1
            
            if p_code == swe.TRUE_NODE:
                ketu_deg = (degree + 180) % 360
                ketu_sign_idx = int(ketu_deg / 30)
                ketu_house = ((ketu_sign_idx - lagna_index + 12) % 12) + 1
                kundli_data["Planets"]["Ketu"] = {"sign": zodiacs[ketu_sign_idx], "degree": round(ketu_deg % 30, 2), "house": ketu_house}
                
            kundli_data["Planets"][p_name] = {"sign": sign, "degree": round(degree % 30, 2), "house": house}
            
        # ==========================================
        # 🌟 VIMSHOTTARI DASHA ENGINE
        # ==========================================
        dasha_lords = ['Ketu', 'Shukra', 'Surya', 'Chandra', 'Mangal', 'Rahu', 'Guru', 'Shani', 'Budh']
        dasha_years = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        
        nakshatra_passed = moon_absolute_degree / (360.0 / 27.0)
        nakshatra_idx = int(nakshatra_passed)
        nakshatra_fraction = nakshatra_passed - nakshatra_idx
        
        lord_idx = nakshatra_idx % 9
        birth_lord = dasha_lords[lord_idx]
        lord_years = dasha_years[lord_idx]
        
        years_passed_at_birth = nakshatra_fraction * lord_years
        balance_years = lord_years - years_passed_at_birth
        
        now = datetime.now()
        days_diff = (now - ist_time).days
        years_lived = days_diff / 365.25
        
        current_md = ""
        current_ad = ""
        
        if years_lived < balance_years:
            current_md = birth_lord
            years_into_md = years_lived + years_passed_at_birth
            ad_idx = lord_idx
            ad_y = 0
            while True:
                ad_length = (lord_years * dasha_years[ad_idx]) / 120.0
                if ad_y + ad_length > years_into_md:
                    current_ad = dasha_lords[ad_idx]
                    break
                ad_y += ad_length
                ad_idx = (ad_idx + 1) % 9
        else:
            y = balance_years
            idx = (lord_idx + 1) % 9
            while True:
                if y + dasha_years[idx] > years_lived:
                    current_md = dasha_lords[idx]
                    years_into_md = years_lived - y
                    ad_y = 0
                    ad_idx = idx
                    while True:
                        ad_length = (dasha_years[idx] * dasha_years[ad_idx]) / 120.0
                        if ad_y + ad_length > years_into_md:
                            current_ad = dasha_lords[ad_idx]
                            break
                        ad_y += ad_length
                        ad_idx = (ad_idx + 1) % 9
                    break
                y += dasha_years[idx]
                idx = (idx + 1) % 9
                
        kundli_data['Vimshottari'] = {"Mahadasha": current_md, "Antardasha": current_ad}

        return jsonify({"status": "success", "kundli": kundli_data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
