SET_PAGE_CONFIG = {
    "page_title": "RaceLive Test Version",
    "page_icon": "🚗",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

HIDE_ST_STYLE = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
				.appview-container .main .block-container{
                            padding-top: 1rem;
                            padding-right: 2rem;
                            padding-left: 2rem;
                            padding-bottom: 1rem;
                        }  
                        .reportview-container {
                            padding-top: 0rem;
                            padding-right: 2rem;
                            padding-left: 2rem;
                            padding-bottom: 0rem;
                        }
                        header[data-testid="stHeader"] {
                            z-index: -1;
                        }
                        div[data-testid="stToolbar"] {
                        z-index: 100;
                        }
                        div[data-testid="stDecoration"] {
                        z-index: 100;
                        }
                        
                        /* サイドバーの幅を狭くする */
                        .css-1d391kg {
                            width: 280px;
                        }
                        
                        section[data-testid="stSidebar"] {
                            width: 280px !important;
                            min-width: 280px !important;
                        }
                        
                        .css-1aumxhk {
                            max-width: 280px;
                        }
                        
                        /* サイドバーが閉じた時のメインコンテンツの調整 */
                        .css-1544g2n {
                            padding-left: 1rem;
                        }
                        
                        /* サイドバーが閉じた状態でのメイン領域を全幅に */
                        .css-18e3th9 {
                            padding-left: 0px;
                        }
                        
                        /* メインコンテンツエリアの調整 */
                        .main .block-container {
                            max-width: none;
                            padding-left: 2rem;
                            padding-right: 2rem;
                        }
                        
                        /* サイドバーが非表示の時のメインエリア調整 */
                        section[data-testid="stSidebar"][aria-expanded="false"] ~ .main {
                            margin-left: 0px !important;
                        }
                        
                        /* サイドバーが表示されている時のメインエリア調整 */
                        section[data-testid="stSidebar"][aria-expanded="true"] ~ .main {
                            margin-left: 250px !important;
                        }
                        
                        /* より広範囲な調整 - サイドバーが閉じた時 */
                        .stApp > div:first-child {
                            margin-left: 0px !important;
                        }
                        
                        /* メインコンテンツエリアの幅を動的に調整 */
                        .main {
                            transition: margin-left 0.3s ease;
                        }
                        
                        /* サイドバーが非表示の時の幅調整 */
                        .css-1y4p8pa, .css-12oz5g7, .css-1rs6os {
                            max-width: 100% !important;
                            width: 100% !important;
                        }
                </style>
"""
