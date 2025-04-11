user_agents = {
    "mobile": {
        "android": {
            "chrome": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
            "opera": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36 OPR/76.0.4017.123",
        },
        "iphone": {
            "safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "firefox": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) Gecko/117.0 Firefox/117.0",
            "opera": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) OPT/4.0.1 Mobile/15E148 Safari/604.1",
        },
    },
    "tablet": {
        "android": {
            "chrome": "Mozilla/5.0 (Linux; Android 11; SM-T865) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "opera": "Mozilla/5.0 (Linux; Android 11; SM-T865) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/76.0.4017.123",
        },
        "ipad": {
            "safari": "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "firefox": "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X; rv:117.0) Gecko/117.0 Firefox/117.0",
            "opera": "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) OPT/4.0.1 Mobile/15E148 Safari/604.1",
        },
    },
    "desktop": {
        "windows": {
            "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0",
            "edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "opera": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/76.0.4017.123",
            "yandex": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 YaBrowser/23.1.3.703 Yowser/2.5 Safari/537.36",
        },
        "mac": {
            "safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "firefox": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1; rv:117.0) Gecko/20100101 Firefox/117.0",
            "edge": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "opera": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/76.0.4017.123",
            "yandex": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 YaBrowser/23.1.3.703 Yowser/2.5 Safari/537.36",
        },
        "linux": {
            "chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "firefox": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:117.0) Gecko/20100101 Firefox/117.0",
            "opera": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/76.0.4017.123",
            "edge": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "yandex": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 YaBrowser/23.1.3.703 Yowser/2.5 Safari/537.36",
        },
    },
    "xr": {
        "oculus_quest2": {
            "oculusbrowser": "Mozilla/5.0 (Linux; Android 10; Quest 2) AppleWebKit/537.36 (KHTML, like Gecko) OculusBrowser/18.1.0.9.462.263726348 Chrome/83.0.4103.122 Safari/537.36",
            "chrome": "Mozilla/5.0 (Linux; Android 10; Quest 2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.88 Mobile Safari/537.36",
        },
        "vision_pro": {
        # Safari: изменяет размер рабочей области
        # - min: 829 x 743 px
        # - max: 1782 x 1188 px
        "safari": "Mozilla/5.0 (VisionOS; AppleVisionPro) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",

        # Edge: 1194 x 743 px
        "edge": "Mozilla/5.0 (VisionOS; AppleVisionPro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",

        # Firefox: 1194 x 711 px
        "firefox": "Mozilla/5.0 (VisionOS; AppleVisionPro; rv:117.0) Gecko/20100101 Firefox/117.0",
        },

        "vive": {
            "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Vive/SteamVR",
        },
        "psvr": {
            "webkit": "Mozilla/5.0 (PlayStation 4 3.11) AppleWebKit/537.73 (KHTML, like Gecko)",
        },
        "valve_index": {
            "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Valve/SteamVR",
        },
        "pico_neo": {
            "chrome": "Mozilla/5.0 (Linux; Android 8.1.0; PICO G2 4K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.99 Safari/537.36",
        },
        "gear_vr": {
            "samsung_browser": "Mozilla/5.0 (Linux; Android 7.0; SM-R323) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/4.0 Chrome/51.0.2704.106 Mobile VR Safari/537.36",
        },
        "daydream": {
            "chrome": "Mozilla/5.0 (Linux; Android 8.0.0; Pixel) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile VR Safari/537.36",
        },
    },
}
