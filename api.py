from flask import Flask, request, jsonify
import swisseph as swe
from geopy.geocoders import Nominatim

app = Flask(__name__)
geolocator = Nominatim(user_agent="supreme_astro_engine_2026")

@app.route('/get_kundli', methods=['POST'])
def get_kundli():
    try:
        data = request.json
        dob = data.get('dob') 
        tob = data.get('tob') 
        place = data.get('place') 
        
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"status": "error", "message": "Shahar ka naam nahi mila."})
            
        lat, lon = location.latitude, location.longitude
        
        year, month, day = map(int, dob.split('-'))
        hour, minute = map(int, tob.split(':'))
        
        hour_utc = hour - 5
        minute_utc = minute - 30
        if minute_utc < 0:
            minute_utc += 60
            hour_utc -= 1
        if hour_utc < 0:
            hour_utc += 24
            day -= 1
            
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        jd = swe.julday(year, month, day, hour_utc + (minute_utc/60.0))
        
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        lagna_degree = ascmc[0]
        zodiacs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        # Lagna ka index nikalna (0 se 11)
        lagna_index = int(lagna_degree / 30)
        lagna_sign = zodiacs[lagna_index]
        
        planets = {
            "Surya": swe.SUN, "Chandra": swe.MOON, 
            "Mangal": swe.MARS, "Budh": swe.MERCURY,
            "Guru": swe.JUPITER, "Shukra": swe.VENUS,
            "Shani": swe.SATURN, "Rahu": swe.TRUE_NODE
        }
        
        kundli_data = {"Lagna": lagna_sign, "Planets": {}}
        
        for p_name, p_code in planets.items():
            pos, _ = swe.calc_ut(jd, p_code)
            degree = pos[0]
            sign_index = int(degree / 30)
            sign = zodiacs[sign_index]
            
            # PERFECT HOUSE (BHAV) CALCULATION FORMULA
            house = ((sign_index - lagna_index + 12) % 12) + 1
            
            if p_code == swe.TRUE_NODE:
                ketu_deg = (degree + 180) % 360
                ketu_sign_idx = int(ketu_deg / 30)
                ketu_house = ((ketu_sign_idx - lagna_index + 12) % 12) + 1
                kundli_data["Planets"]["Ketu"] = {"sign": zodiacs[ketu_sign_idx], "degree": round(ketu_deg % 30, 2), "house": ketu_house}
                
            kundli_data["Planets"][p_name] = {"sign": sign, "degree": round(degree % 30, 2), "house": house}
            
        return jsonify({
            "status": "success",
            "kundli": kundli_data
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
