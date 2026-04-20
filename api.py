from flask import Flask, request, jsonify
import swisseph as swe
from geopy.geocoders import Nominatim
import time

app = Flask(__name__)
geolocator = Nominatim(user_agent="supreme_astro_engine_2026")

@app.route('/get_kundli', methods=['POST'])
def get_kundli():
    try:
        data = request.json
        dob = data.get('dob') # YYYY-MM-DD
        tob = data.get('tob') # HH:MM
        place = data.get('place') # City Name
        
        # 1. Shahar (City) se Latitude/Longitude nikalna
        location = geolocator.geocode(place)
        if not location:
            return jsonify({"status": "error", "message": "Shahar ka naam nahi mila."})
            
        lat, lon = location.latitude, location.longitude
        
        # 2. Date aur Time todna (IST to UTC)
        year, month, day = map(int, dob.split('-'))
        hour, minute = map(int, tob.split(':'))
        
        hour_utc = hour - 5
        minute_utc = minute - 30
        if minute_utc < 0:
            minute_utc += 60
            hour_utc -= 1
        if hour_utc < 0:
            hour_utc += 24
            day -= 1 # Basic adjustment for midnight
            
        # 3. Astrology Engine Start (Lahiri Ayanamsa)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        jd = swe.julday(year, month, day, hour_utc + (minute_utc/60.0))
        
        # 4. Lagna (Ascendant) nikalna
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        lagna_degree = ascmc[0]
        zodiacs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        lagna_sign = zodiacs[int(lagna_degree / 30)]
        
        # 5. Saare 9 Grah nikalna
        planets = {
            "Surya (Sun)": swe.SUN, "Chandra (Moon)": swe.MOON, 
            "Mangal (Mars)": swe.MARS, "Budh (Mercury)": swe.MERCURY,
            "Guru (Jupiter)": swe.JUPITER, "Shukra (Venus)": swe.VENUS,
            "Shani (Saturn)": swe.SATURN, "Rahu (True Node)": swe.TRUE_NODE
        }
        
        kundli_data = {"Lagna": lagna_sign, "Planets": {}}
        
        for p_name, p_code in planets.items():
            pos, _ = swe.calc_ut(jd, p_code)
            degree = pos[0]
            sign = zodiacs[int(degree / 30)]
            # Ketu is exactly 180 degrees opposite to Rahu
            if p_code == swe.TRUE_NODE:
                ketu_deg = (degree + 180) % 360
                kundli_data["Planets"]["Ketu"] = {"sign": zodiacs[int(ketu_deg / 30)], "degree": round(ketu_deg % 30, 2)}
                
            kundli_data["Planets"][p_name] = {"sign": sign, "degree": round(degree % 30, 2)}
            
        return jsonify({
            "status": "success",
            "kundli": kundli_data
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
