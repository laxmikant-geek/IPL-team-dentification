# IPL Team Identification

A computer vision project to identify IPL teams from images.

## Image Sources

Raw images are scraped from ESPN Cricinfo team photo galleries using `download_images.py`.

| Team Code | Team Name | Source URL |
|-----------|-----------|------------|
| `RR` | Rajasthan Royals | https://www.espncricinfo.com/team/rajasthan-royals-335977/photo |
| `RCB` | Royal Challengers Bengaluru | https://www.espncricinfo.com/team/royal-challengers-bengaluru-335970/photo |
| `SRH` | Sunrisers Hyderabad | https://www.espncricinfo.com/team/sunrisers-hyderabad-628333/photo |
| `CSK` | Chennai Super Kings | https://www.espncricinfo.com/team/chennai-super-kings-335973/photo |
| `DC` | Delhi Capitals | https://www.espncricinfo.com/team/delhi-capitals-333979/photo |
| `GT` | Gujarat Titans | https://www.espncricinfo.com/team/gujarat-titans-1298423/photo |
| `KKR` | Kolkata Knight Riders | https://www.espncricinfo.com/team/kolkata-knight-riders-381943/photo |
| `LSG` | Lucknow Super Giants | https://www.espncricinfo.com/team/lucknow-super-giants-1298541/photo |
| `MI` | Mumbai Indians | https://www.espncricinfo.com/team/mumbai-indians-335974/photo |
| `PBKS` | Punjab Kings | https://www.espncricinfo.com/team/punjab-kings-335976/photo |
| `IPL` | IPL 2025 Series Gallery | https://www.espncricinfo.com/series/ipl-2025-1449924/photo |

- **Image CDN pattern:** `https://img1.hscicdn.com/image/upload/...` (e.g. `414800.jpg`, `414852.png`)

## Setup

```bash
pip install selenium webdriver-manager requests beautifulsoup4
```

## Downloading Images

Use `--team` (required) to choose a team and `--year` (default: 2025) to filter by season.

```bash
# Download 2025 images for Rajasthan Royals → raw-images/RR/
python download_images.py --team RR

# Download 2025 images for Royal Challengers Bengaluru → raw-images/RCB/
python download_images.py --team RCB

# Download 2025 images for Sunrisers Hyderabad → raw-images/SRH/
python download_images.py --team SRH

# Download a different year
python download_images.py --team RR --year 2024

# Override output directory
python download_images.py --team CSK --out raw-images/csk

# Override gallery URL
python download_images.py --team IPL --url https://www.espncricinfo.com/series/ipl-2025-1449924/photo

# Slow down scrolling on a slow connection
python download_images.py --team RCB --scroll-pause 3
```

### All Options

| Flag | Default | Description |
|------|---------|-------------|
| `--team` | *(required)* | Team code: `RR`, `RCB`, `SRH`, `CSK`, `DC`, `GT`, `KKR`, `LSG`, `MI`, `PBKS`, `IPL` |
| `--year` | `2025` | Only download photos from this year |
| `--out` | per-team folder | Override output directory |
| `--url` | per-team URL | Override gallery page URL |
| `--scroll-pause` | `2.0` | Seconds to wait between scroll steps |

## Folder Structure

```
raw-images/
├── csk/              # Chennai Super Kings
├── Delhi capitals/   # Delhi Capitals
├── RCB/              # Royal Challengers Bengaluru
├── RR/               # Rajasthan Royals
├── SRH/              # Sunrisers Hyderabad
├── GT/               # Gujarat Titans
├── KKR/              # Kolkata Knight Riders
├── LSG/              # Lucknow Super Giants
├── MI/               # Mumbai Indians
├── PBKS/             # Punjab Kings
├── no team/          # Images with no visible team
└── downloaded/       # IPL series gallery (--team IPL)
```
