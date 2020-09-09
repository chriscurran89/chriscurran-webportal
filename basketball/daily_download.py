from nba_ref import NBARef


yesterday = NBARef().yesterday_box()
yesterday.to_csv('~/Documents/chris-curran-portfolio/nba_ref/daily_download/yesterday.csv', index=False)

window7 = NBARef().window_box(7)
window7.to_csv('~/Documents/chris-curran-portfolio/nba_ref/daily_download/window7.csv', index=False)

window15 = NBARef().window_box(15)
window15.to_csv('~/Documents/chris-curran-portfolio/nba_ref/daily_download/window15.csv', index=False)

window30 = NBARef().window_box(30)
window30.to_csv('~/Documents/chris-curran-portfolio/nba_ref/daily_download/window30.csv', index=False)

print("...daily download complete...")
