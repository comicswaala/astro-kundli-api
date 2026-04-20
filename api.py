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
        
        # 1. Location Fetch
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
            
        # 3. Swiss Ephemeris Setup (Vedic Mode)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        jd = swe.julday(year, month, day, hour_utc + (minute_utc/60.0))
        ayanamsa = swe.get_ayanamsa_ut(jd)
        sidereal_flag = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        
        # 4. Houses & Lagna (Sidereal)
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        lagna_degree = (ascmc[0] - ayanamsa) % 360
        zodiacs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        lagna_index = int(lagna_degree / 30)
        lagna_sign = zodiacs[lagna_index]
        
        planets = {
            "Surya": swe.SUN, "Chandra": swe.MOON, "Mangal": swe.MARS, 
            "Budh": swe.MERCURY, "Guru": swe.JUPITER, "Shukra": swe.VENUS,
            "Shani": swe.SATURN, "Rahu": swe.TRUE_NODE
        }
        
        kundli_data = {"Lagna": lagna_sign, "Planets": {}}
        moon_absolute_degree = 0
        
        for p_name, p_code in planets.items():
            pos, _ = swe.calc_ut(jd, p_code, sidereal_flag) 
            degree = pos[0]
            if p_code == swe.MOON: moon_absolute_degree = degree
                
            sign_index = int(degree / 30)
            sign = zodiacs[sign_index]
            house = ((sign_index - lagna_index + 12) % 12) + 1
            
            if p_code == swe.TRUE_NODE:
                k_deg = (degree + 180) % 360
                k_s_idx = int(k_deg / 30)
                kundli_data["Planets"]["Ketu"] = {"sign": zodiacs[k_s_idx], "degree": round(k_deg % 30, 2), "house": ((k_s_idx - lagna_index + 12) % 12) + 1}
                
            kundli_data["Planets"][p_name] = {"sign": sign, "degree": round(degree % 30, 2), "house": house}
            
        # 5. Vimshottari Dasha Engine (MD, AD, PD)
        d_lords = ['Ketu', 'Shukra', 'Surya', 'Chandra', 'Mangal', 'Rahu', 'Guru', 'Shani', 'Budh']
        d_years = [7, 20, 6, 10, 7, 18, 16, 19, 17]
        
        n_passed = moon_absolute_degree / (360.0 / 27.0)
        n_idx = int(n_passed)
        n_frac = n_passed - n_idx
        
        l_idx = n_idx % 9
        balance = (1 - n_frac) * d_years[l_idx]
        y_lived = (datetime.now() - ist_time).days / 365.25
        
        curr_md = ""; curr_ad = ""; curr_pd = ""
        
        # Dasha Logic Loop
        y_sum = balance - d_years[l_idx] 
        found_md = False
        for i in range(100):
            idx = (l_idx + i) % 9
            md_len = d_years[idx]
            if y_sum + md_len > y_lived:
                curr_md = d_lords[idx]
                y_in_md = y_lived - y_sum
                # Antardasha
                ad_sum = 0
                for j in range(9):
                    ad_idx = (idx + j) % 9
                    ad_len = (d_years[idx] * d_years[ad_idx]) / 120.0
                    if ad_sum + ad_len > y_in_md:
                        curr_ad = d_lords[ad_idx]
                        y_in_ad = y_in_md - ad_sum
                        # Pratayantardasha
                        pd_sum = 0
                        for k in range(9):
                            pd_idx = (ad_idx + k) % 9
                            pd_len = (d_years[idx] * d_years[ad_idx] * d_years[pd_idx]) / (120.0 * 120.0)
                            if pd_sum + pd_len > y_in_ad:
                                curr_pd = d_lords[pd_idx]
                                break
                            pd_sum += pd_len
                        break
                    ad_sum += ad_len
                break
            y_sum += md_len

        kundli_data['Vimshottari'] = {"Mahadasha": curr_md, "Antardasha": curr_ad, "Pratayantardasha": curr_pd}
        return jsonify({"status": "success", "kundli": kundli_data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
