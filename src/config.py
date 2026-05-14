"""來源清單與標籤關鍵字字典。"""

RSS_SOURCES = [
    # 國外英文主流
    {"name": "The Hacker News", "url": "https://feeds.feedburner.com/TheHackersNews", "lang": "en"},
    {"name": "Bleeping Computer", "url": "https://www.bleepingcomputer.com/feed/", "lang": "en"},
    {"name": "Krebs on Security", "url": "https://krebsonsecurity.com/feed/", "lang": "en"},
    {"name": "Dark Reading", "url": "https://www.darkreading.com/rss.xml", "lang": "en"},
    {"name": "SecurityWeek", "url": "https://www.securityweek.com/feed/", "lang": "en"},
    # 台灣中文媒體
    {"name": "iThome Security", "url": "https://www.ithome.com.tw/rss/category/513", "lang": "zh"},
]

# NVD 最近 CVE JSON feed；門檻在 fetchers.nvd 內處理
NVD_RECENT_FEED = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_MIN_CVSS = 7.0

# 標籤關鍵字字典：value 為 (中英關鍵字 list, 重要性權重)
# 權重越高代表越優先推播；同一篇可命中多 tag，取最高權重排序
TAG_RULES = {
    "#零日": (
        ["zero-day", "zero day", "0-day", "0day", "零日"],
        100,
    ),
    "#勒索軟體": (
        ["ransomware", "ransom", "locker", "勒索", "勒索軟體"],
        90,
    ),
    "#APT": (
        ["apt group", "apt-", "nation-state", "state-sponsored", "lazarus", "kimsuky",
         "fancy bear", "cozy bear", "apt28", "apt29", "apt38", "apt41"],
        85,
    ),
    "#資料外洩": (
        ["data breach", "data leak", "leaked", "exposed database", "資料外洩", "個資外洩", "外洩"],
        80,
    ),
    "#供應鏈": (
        ["supply chain", "supply-chain", "npm package", "pypi", "malicious package", "供應鏈"],
        78,
    ),
    "#CVE": (
        ["cve-"],
        75,
    ),
    "#漏洞": (
        ["vulnerability", "vulnerabilities", "exploit", "rce", "remote code execution",
         "privilege escalation", "sql injection", "xss", "csrf",
         "漏洞", "弱點", "提權"],
        70,
    ),
    "#補丁": (
        ["patch tuesday", "security update", "advisory", "hotfix", "patched",
         "更新", "修補", "資安公告"],
        60,
    ),
    "#惡意軟體": (
        ["malware", "trojan", "backdoor", "rootkit", "spyware", "stealer",
         "惡意程式", "木馬", "後門"],
        65,
    ),
    "#釣魚": (
        ["phishing", "smishing", "vishing", "scam", "fraud",
         "釣魚", "詐騙", "假冒"],
        55,
    ),
    "#雲端": (
        ["aws", "azure", "gcp", "google cloud", "s3 bucket", "kubernetes", "k8s",
         "container escape", "cloud security", "雲端"],
        50,
    ),
    "#Web": (
        ["wordpress", "plugin", "web server", "nginx", "apache", "owasp",
         "網站", "外掛"],
        45,
    ),
    "#行動裝置": (
        ["android", "ios", "iphone", "mobile malware", "google play", "app store",
         "行動裝置", "手機"],
        45,
    ),
    "#工具": (
        ["github", "open source tool", "released", "new tool", "framework",
         "released tool"],
        30,
    ),
}

# 一般標籤都比不上的「兜底」標籤
FALLBACK_TAG = "#資安"
