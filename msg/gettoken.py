
import requests
import json


def main():
        
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=COD2E7QDOIci3GtkCGbDKgAv&client_secret=7Kjm7eEZiFvOUR267SO7rEUcD6yD5Sm7"
    
    payload = ""
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    print(response.text)
    

if __name__ == '__main__':
    main()

'''
{"refresh_token":"25.8c5aebf824ebb04e033e3a712ad85c2b.315360000.1999759011.282335-33698410","expires_in":2592000,"session_key":"9mzdCrKiyEEOIH9X1wMUv1GkM46glT+1UeYUhTFNu0sq4zVpnXuij+AkHh3Gnb+Y1Q5CRmtP9SFi8F42bkAbv8pgdgPW5w==",
"access_token":"24.16cfa6f4d7b1c98aeab6de34ee819770.2592000.1686991011.282335-33698410",
"scope":"audio_voice_assistant_get public brain_all_scope wise_adapt lebo_resource_base lightservice_public hetu_basic lightcms_map_poi kaidian_kaidian ApsMisTest_Test\u6743\u9650 vis-classify_flower lpq_\u5f00\u653e cop_helloScope ApsMis_fangdi_permission smartapp_snsapi_base smartapp_mapp_dev_manage iop_autocar oauth_tp_app smartapp_smart_game_openapi oauth_sessionkey smartapp_swanid_verify smartapp_opensource_openapi smartapp_opensource_recapi fake_face_detect_\u5f00\u653eScope vis-ocr_\u865a\u62df\u4eba\u7269\u52a9\u7406 idl-video_\u865a\u62df\u4eba\u7269\u52a9\u7406 smartapp_component smartapp_search_plugin avatar_video_test b2b_tp_openapi b2b_tp_openapi_online smartapp_gov_aladin_to_xcx",
"session_secret":"680dd2288d57dc4d8066407abfb37d33"}'''


'''

APPID
33694746
API KEY
COD2E7QDOIci3GtkCGbDKgAv
Secret KEY
7Kjm7eEZiFvOUR267SO7rEUcD6yD5Sm7'''




'''
"24.e86400d61c814d84e39b091c424457e2.2592000.1687010931.282335-33694746"
'''