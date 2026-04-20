from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime

app = Flask(__name__)

@app.route('/get_kundli', methods=['POST'])
def get_kundli():
    try:
        data = request.json
        dob = data.get('dob') # Format: YYYY-MM-DD
        tob = data.get('tob') # Format: HH:MM
        
        # Date aur Time ko todna
        year, month, day = map(int, dob.split('-'))
        hour, minute = map(int, tob.split(':'))
        
        # UTC Time me badalna (Indian time GMT+5:30 hota hai)
        # Note: Ye basic example hai, real me timezone library use hoti hai
        hour_utc = hour - 5
        minute_utc = minute - 30
        if minute_utc < 0:
            minute_utc += 60
            hour_utc -= 1
            
        # Julian Day Calculation (Astrology ka base)
        swe.set_sid_mode(swe.SIDM_LAHIRI) # Lahiri Ayanamsa (Vedic Astrology)
        jd = swe.julday(year, month, day, hour_utc + (minute_utc/60.0))
        
        # 1. Sun (Surya) ki position
        sun_pos, _ = swe.calc_ut(jd, swe.SUN)
        
        # 2. Moon (Chandrama) ki position
        moon_pos, _ = swe.calc_ut(jd, swe.MOON)
        
        # Zodiac Signs (Rashi) array
        zodiacs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        # Chandrama kis Rashi me hai (Moon Sign)
        moon_sign_index = int(moon_pos[0] / 30)
        moon_sign = zodiacs[moon_sign_index]
        
        return jsonify({
            "status": "success",
            "moon_sign": moon_sign,
            "moon_degree": round(moon_pos[0] % 30, 2),
            "sun_degree": round(sun_pos[0] % 30, 2),
            "message": f"Aapki Chandra Rashi {moon_sign} hai."
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)