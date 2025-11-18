import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Laskentademo")


# --- mapping dicts ----
e_moni_pot = {
	"kangas":1.0, "lehto":1.0, "kallio":1.0, "metsa":1.0, "suo":1.0,
	"lahteikko":1.0, "jarvi":1.0, "itameri":1.0, "virtavesi":1.0,
	"p_puisto":1.0, "s_ranta":1.0, "i_ranta":1.0, "uusniitty":1.0,
	"pebi":1.0, "jyrkanne":1.0, "kosteikko":0.9, "ruderaatti":0.8,
	"puutarha":0.7, "pensaikko":0.7, "a_puisto":0.6, "pelto":0.5,
	"maavaraine":0.5, "katu":0.3, "integroitu":0.3, "vayla":0.5,
	"teollinen":0.1, "vesiallas":0.1
}

hy_l_poten = {
	"i_ranta":1.0, "s_ranta":1.0, "pebi":1.0, "jyrkanne":1.0,
	"lehto":1.0, "kangas":1.0, "kallio":1.0, "metsa":1.0,
	"lahteikko":1.0, "p_puisto":0.95, "puutarha":0.85,
	"itameri":0.8, "jarvi":0.8, "virtavesi":0.8, "suo":0.8,
	"a_puisto":0.79, "uusniitty":0.75, "vesiallas":0.73,
	"kosteikko":0.73, "maavaraine":0.55, "pelto":0.5,
	"katu":0.5, "integroitu":0.35, "pensaikko":0.27,
	"ruderaatti":0.25, "vayla":0.2, "teollinen":0.0
}

pi_l_viile = {
	"itameri":1.0, "metsa":1.0, "lehto":1.0, "kangas":1.0,
	"kallio":1.0, "suo":1.0, "lahteikko":1.0, "jarvi":1.0,
	"vesiallas":0.7, "p_puisto":0.7, "kosteikko":0.7,
	"s_ranta":0.7, "i_ranta":0.7, "virtavesi":0.7,
	"maavaraine":0.7, "vayla":0.7, "pebi":0.7,
	"puutarha":0.5, "pensaikko":0.5, "katu":0.5,
	"ruderaatti":0.5, "a_puisto":0.3, "pelto":0.3,
	"uusniitty":0.3, "teollinen":0.3, "integroitu":0.3,
	"jyrkanne":0.3
}

hi_l_sitom = {
	"a_puisto":0.4, "i_ranta":0.5, "integroitu":0.05, "itameri":0.7,
	"jyrkanne":0.05, "jarvi":0.7, "kallio":0.9, "kangas":0.9,
	"katu":0.15, "kosteikko":0.5, "lahteikko":0.6, "lehto":0.9,
	"maavaraine":0.4, "metsa":0.9, "p_puisto":0.7, "pebi":0.4,
	"pelto":0.3, "pensaikko":0.55, "puutarha":0.3, "ruderaatti":0.35,
	"s_ranta":0.6, "suo":0.9, "teollinen":0.1, "uusniitty":0.25,
	"vayla":0.25, "vesiallas":0.0, "virtavesi":0.2
}

hu_l_halli = {
	"kangas":1.0, "kosteikko":1.0, "lahteikko":1.0, "lehto":1.0,
	"metsa":1.0, "suo":1.0, "virtavesi":1.0, "jarvi":0.9,
	"i_ranta":0.85, "kallio":0.85, "s_ranta":0.85, "p_puisto":0.75,
	"pensaikko":0.75, "vayla":0.75, "itameri":0.7, "vesiallas":0.7,
	"katu":0.6, "pebi":0.55, "puutarha":0.55, "uusniitty":0.55,
	"a_puisto":0.45, "maavaraine":0.45, "ruderaatti":0.45,
	"integroitu":0.35, "jyrkanne":0.35, "pelto":0.35, "teollinen":0.35
}

all_types = sorted(set().union(
	e_moni_pot.keys(), hy_l_poten.keys(), pi_l_viile.keys(), hi_l_sitom.keys(), hu_l_halli.keys()
))

# --- selkokieli (human-readable) mapping for all keys in mapping dicts
def _humanize_key(k: str) -> str:
	# Basic transformation: replace underscores with spaces and title-case
	s = k.replace('_', ' ')
	# common abbreviations: p_ -> pieni/puisto markers are ambiguous, keep simple
	s = s.replace(' p ', ' p ')  # noop placeholder for future rules
	return s.capitalize()

all_keys = set(all_types)
# include soil keys too
all_keys.update([
	'vesi','lohkareet','isot kivet','pienet kivet','sora','hiekka','soramoreeni','hieno hieta',
	'karkea hieta','hiekkamoreeni','moreeni','moreenimuodostuma','drumliini','rahkaturve','turve',
	'täytemaa','kallioinen alue','hiesu','siltti','savi','liejuinen hieno hieta','liejuhiesu',
	'liejusavi','lieju','saraturve'
])

# build selkokieli dict with fallbacks
selkokieli = {k: _humanize_key(k) for k in all_keys}
# manual overrides for a few common codes to make them clearer
manual = {
	'p_puisto': 'Puustoinen puisto',
	'a_puisto': 'Avoin puisto',
	'i_ranta': 'Merenranta',
	's_ranta': 'Sisävesiranta',
	'jarvi': 'Järvi',
	'itameri': 'Meri',
	'virtavesi': 'Virtavesi',
	'vesiallas': 'Vesiallas',
	'kosteikko': 'Kosteikko',
	'uusniitty': 'Uusniitty',
	'kangas': 'Kangas',
	'lehto': 'Lehto',
	'kallio': 'Kallio',
	'metsa': 'Metsä',
	'pelto': 'Pelto',
	'puutarha': 'Puutarha',
	'pensaikko': 'Pensaikko',
	'teollinen': 'Teollinen alue',
	'katu': 'Liikennealue',
}
selkokieli.update(manual)

st.markdown("Valitse luontotyypit ja anna kullekin pinta-ala ja lisätiedot.")

# Build options in same order as all_types (human labels)
options = [selkokieli[k] for k in all_types]

# Show human-readable labels; default must be from options
selected_selko = st.multiselect("Valitse luontotyypit", options=options, default=options[:1])

# Map chosen human labels back to original keys (preserve all_types order)
selected = [k for k in all_types if selkokieli[k] in selected_selko]

if not selected:
	st.info("Valitse vähintään yksi luontotyyppi.")
	st.stop()

# soil/ground type options from hu_m_lapai mapping (create mapping here)
hu_m_lapai = {
	"vesi":1.0, "lohkareet":1.0, "isot kivet":1.0, "pienet kivet":1.0,
	"sora":1.0, "hiekka":1.0, "soramoreeni":0.7, "hieno hieta":0.7,
	"karkea hieta":0.7, "hiekkamoreeni":0.4, "moreeni":0.4,
	"moreenimuodostuma":0.4, "drumliini":0.4, "rahkaturve":0.4,
	"turve":0.4, "täytemaa":0.4, "kallioinen alue":0.2,
	"hiesu":0.1, "siltti":0.1, "savi":0.1,
	"liejuinen hieno hieta":0.1, "liejuhiesu":0.1, "liejusavi":0.1,
	"lieju":0.1, "saraturve":0.1
}

rows = []
for t in selected:
	with st.container(border=True):
		# human-readable label for UI
		hr = selkokieli.get(t, t)
		st.markdown(f"### {hr}")
		# defaults from mapping dicts
		default_emp = e_moni_pot.get(t, 0.5)
		default_hlh = hu_l_halli.get(t, 0.5)
		default_plv = pi_l_viile.get(t, 0.5)
		default_hls = hi_l_sitom.get(t, 0.5)
		default_hyp = hy_l_poten.get(t, 0.5)

		c1, c2, c3, c4 = st.columns([2,1,1,1])
		# colors for small containers
		col_styles = {
			'area': '#f7fcff',
			'latvus': '#f6fff7',
			'twi': '#fffaf0',
			'etila': '#fff7fb',
			'hy': '#f7fff6'
		}
		use_border = True
		with c1:
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['area']};padding:8px;border-radius:6px'>Pinta-ala ({hr})</div>", unsafe_allow_html=True)
				area = st.number_input(f"Pinta-ala ({hr}) [m2]", min_value=0.0, value=100.0, step=10.0, key=f"area_{t}")
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['area']};padding:8px;border-radius:6px'>Maa / lähde ({hr})</div>", unsafe_allow_html=True)
				p_maalaji = st.selectbox(f"Maa/lahde ({hr})", options=sorted(list(hu_m_lapai.keys())), index=0, key=f"maalaji_{t}")
		with c2:
			with st.container(border=use_border):
				p_latvus = st.slider(f"Latvus% ({hr})", 0.0, 100.0, 50.0, step=1.0, key=f"latvus_{t}")
				p_twi = st.slider(f"TWI ({hr})", 0.0, 20.0, 5.0, step=0.1, key=f"twi_{t}")
		with c3:
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['etila']};padding:8px;border-radius:6px'>Ekologinen tila ({hr})</div>", unsafe_allow_html=True)
				e_tila = st.slider(f"Ekologinen tila (e_tila) ({hr})", 0.0, 1.0, float(default_emp), step=0.01, key=f"etila_{t}")
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['etila']};padding:8px;border-radius:6px'>Ranta ({hr})</div>", unsafe_allow_html=True)
				p_ranta = st.checkbox(f"Ranta (p_ranta) ({hr})", value=False, key=f"ranta_{t}")
		with c4:
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['hy']};padding:8px;border-radius:6px'>Saavutettavuus ({hr})</div>", unsafe_allow_html=True)
				hy_saavute = st.slider(f"Hyvä saavutettavuus ({hr})", 0.0, 1.0, 0.0, step=0.01, key=f"saav_{t}")
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['hy']};padding:8px;border-radius:6px'>Maisema ({hr})</div>", unsafe_allow_html=True)
				hy_maisema = st.slider(f"Hyvä maisema ({hr})", 0.0, 1.0, 0.0, step=0.01, key=f"mai_{t}")
			with st.container(border=use_border):
				st.markdown(f"<div style='background:{col_styles['hy']};padding:8px;border-radius:6px'>Kohokohdat ({hr})</div>", unsafe_allow_html=True)
				hy_kohokoh = st.slider(f"Hyvät kohokohdat ({hr})", 0.0, 1.0, 0.0, step=0.01, key=f"koh_{t}")

	rows.append({
		"luontotyyppi": t,
		"kokonaisala": area,
		"p_maalaji": p_maalaji,
		"p_latvus%": p_latvus,
		"p_TWI": p_twi,
		"e_tila": e_tila,
		"hy_saavute": hy_saavute,
		"hy_maisema": hy_maisema,
		"hy_kohokoh": hy_kohokoh,
		"p_ranta": int(p_ranta)
	})

df = pd.DataFrame(rows)
if df.empty:
	st.info("Ei rivejä laskettavaksi")
	st.stop()

# sliders for total-area multiplier and non-evaluated-area factor
col1, _ = st.columns(2)
with col1:
	# Allow the user to set the estimated total area (m2) for normalization
	if 'area_input' not in st.session_state:
		st.session_state.area_input = int(df['kokonaisala'].sum())

	st.markdown("---")
	st.session_state.area_input = st.number_input('**Kohteen kokonaisala (m2)**', min_value=int(df['kokonaisala'].sum()), value=st.session_state.area_input, step=10)

def calc_p_lat_arvo(p_lat):
	if p_lat < 25:
		return 0.10
	if p_lat < 50:
		return 0.50
	if p_lat < 75:
		return 0.70
	return 1.00

def calc_hu_m_koste(twi):
	if twi < 6:
		return 0.30
	if twi < 10:
		return 0.80
	return 1.00

# compute KP values per row following the QGIS script logic
out_rows = []
for _, r in df.iterrows():
	lt = r['luontotyyppi']
	area = r['kokonaisala']
	p_ma = r['p_maalaji']
	p_lat = r['p_latvus%'] or 0
	p_twi = r['p_TWI'] or 0
	et = r.get('e_tila', 0) or 0
	saav = r.get('hy_saavute', 0) or 0
	mai = r.get('hy_maisema', 0) or 0
	koh = r.get('hy_kohokoh', 0) or 0
	p_ranta = int(r.get('p_ranta', 0) or 0)

	pl = calc_p_lat_arvo(p_lat)
	emp = e_moni_pot.get(lt, 0)
	lumo_kp = emp * et
	hlh = hu_l_halli.get(lt, 0)
	hmk = calc_hu_m_koste(p_twi)
	hml = hu_m_lapai.get(p_ma, 0)

	if lt in ("jarvi","virtavesi","lahteikko","itameri","vesiallas"):
		kp_hu = hlh
	elif lt in ("pelto","uusniitty","a_puisto","kosteikko"):
		kp_hu = hlh * ((hmk + hml) / 2 if (hmk + hml) else 0)
	else:
		kp_hu = ((2*hlh + hmk) / 3) * ((hml + pl) / 2 if (hml + pl) else 0)

	plv = pi_l_viile.get(lt, 0)
	if lt in ("jarvi","virtavesi","lahteikko","itameri","vesiallas",
			  "pelto","uusniitty","a_puisto","kosteikko"):
		kp_pi = plv
	else:
		kp_pi = plv * pl

	hls = hi_l_sitom.get(lt, 0)
	if lt in ("jarvi","virtavesi","lahteikko","itameri","vesiallas",
			  "pelto","uusniitty","a_puisto","kosteikko"):
		kp_hi = hls
	else:
		kp_hi = hls * pl

	ilm_kp = (kp_hu + kp_pi + kp_hi) / 3

	hyp = hy_l_poten.get(lt, 0)
	if p_ranta == 1:
		hyp = 1.0

	hyv_kp = hyp * (lumo_kp + ilm_kp + saav + mai + koh) / 5

	out_rows.append({
		'LUONTOTYYPPI': lt,
		'kokonaisala': area,
		'lumo_kp': round(lumo_kp, 4),
		'kp_hu': round(kp_hu, 4),
		'kp_pi': round(kp_pi, 4),
		'kp_hi': round(kp_hi, 4),
		'ilm_kp': round(ilm_kp, 4),
		'hy_l_poten': round(hyp, 4),
		'hyvinvo_kp': round(hyv_kp, 4),
		'ekotehokas_lumo': round(lumo_kp * area, 2),
		'ekotehokas_ilm': round(ilm_kp * area, 2),
		'ekotehokas_hyv': round(hyv_kp * area, 2),
	})

out_df = pd.DataFrame(out_rows)

if out_df.empty:
	st.info('Ei laskettuja rivejä')
	st.stop()

# Use the provided total_area_input as the denominator for normalization
total_area = st.session_state.area_input
non_arvo_area = max(0, total_area - int(out_df['kokonaisala'].sum()))
if non_arvo_area > 0:
	# add a placeholder row for the non-evaluated area with zeroed coefficients
	out_df = pd.concat([
		out_df,
		pd.DataFrame([{ 
			'LUONTOTYYPPI': 'arvioimaton alue',
			'kokonaisala': non_arvo_area,
			'lumo_kp': 0,
			'kp_hu': 0,
			'kp_pi': 0,
			'kp_hi': 0,
			'ilm_kp': 0,
			'hy_l_poten': 0,
			'hyvinvo_kp': 0,
			'ekotehokas_lumo': 0,
			'ekotehokas_ilm': 0,
			'ekotehokas_hyv': 0,
		}])
	], ignore_index=True)

def sunburst_from(df, value_col, title, total_area=None):
	# Create normalized sunburst if total_area is provided (>0). Otherwise use absolute areas.
	d = df[[ 'LUONTOTYYPPI', 'kokonaisala', value_col]].copy()
	if total_area and total_area > 0:
		# normalize kokonaiala and ekotehokas to fraction of total area
		d['kokonaisala_norm'] = d['kokonaisala'] / float(total_area)
		d['ekotehokas_ala'] = d[value_col] / float(total_area)
		# Ensure ekotehokas does not exceed the available area fraction
		d['ekotehokas_ala'] = d[['ekotehokas_ala', 'kokonaisala_norm']].min(axis=1).clip(lower=0)
		d['PÄÄLUOKKA'] = 'Arvot'
		# Build 'Arvot' rows (actual ekotehokas per luontotyyppi) excluding any placeholder
		arvot = d.loc[d['LUONTOTYYPPI'] != 'arvioimaton alue', ['PÄÄLUOKKA','LUONTOTYYPPI','ekotehokas_ala']].copy()
		# Prefer explicit 'arvioimaton alue' non-evaluated area if present
		non_eval_abs = df.loc[df['LUONTOTYYPPI'] == 'arvioimaton alue', 'kokonaisala'].sum() if 'LUONTOTYYPPI' in df.columns else 0
		if non_eval_abs > 0:
			# use explicit non-evaluated area as Potentiaali (fraction)
			surplus = float(non_eval_abs) / float(total_area)
		else:
			# compute surplus fraction from remaining uncovered area
			sum_selected = arvot['ekotehokas_ala'].sum() if not arvot.empty else 0.0
			surplus = max(0.0, 1.0 - float(d['kokonaisala_norm'].sum()))
		pot = pd.DataFrame([{
			'PÄÄLUOKKA': 'Potentiaali',
			'LUONTOTYYPPI': 'Muu kuin viherrakenne',
			'ekotehokas_ala': surplus
		}])
		combined = pd.concat([arvot, pot], ignore_index=True)
	else:
		d = d.rename(columns={ value_col:'ekotehokas_ala'})
		d['PÄÄLUOKKA'] = 'Arvot'
		# Ensure ekotehokas does not exceed the available area
		d['ekotehokas_ala'] = d[['ekotehokas_ala', 'kokonaisala']].min(axis=1).clip(lower=0)
		# If there is an explicit non-evaluated area row, show it as Potentiaali
		non_eval_abs = df.loc[df['LUONTOTYYPPI'] == 'arvioimaton alue', 'kokonaisala'].sum() if 'LUONTOTYYPPI' in df.columns else 0
		if non_eval_abs > 0:
			pot = pd.DataFrame([{
				'PÄÄLUOKKA': 'Potentiaali',
				'LUONTOTYYPPI': 'Muu kuin viherrakenne',
				'ekotehokas_ala': non_eval_abs
			}])
			combined = pd.concat([d[['PÄÄLUOKKA','LUONTOTYYPPI','ekotehokas_ala']], pot], ignore_index=True)
		else:
			# Potential is the remaining (non-negative) area per-type
			d['potential'] = (d['kokonaisala'] - d['ekotehokas_ala']).clip(lower=0)
			pot = d.copy()
			pot['ekotehokas_ala'] = pot['potential']
			pot['PÄÄLUOKKA'] = 'Potentiaali'
			combined = pd.concat([d, pot], ignore_index=True)

	# Map luontotyyppi codes to human-readable labels for plotting
	if 'LUONTOTYYPPI' in combined.columns:
		combined['LUONTOTYYPPI_LABEL'] = combined['LUONTOTYYPPI'].apply(lambda k: selkokieli.get(k, k) if isinstance(k, str) else k)
	else:
		combined['LUONTOTYYPPI_LABEL'] = combined.get('LUONTOTYYPPI', '')

	fig = px.sunburst(
		combined,
		# Use human-readable labels for luontotyyppi in the plot
		path=['PÄÄLUOKKA','LUONTOTYYPPI_LABEL'],
		values='ekotehokas_ala',
		title=title,
		color='PÄÄLUOKKA',
		color_discrete_map={'Arvot':'darkgreen','Potentiaali':'lightgrey'},
		height=450
	)
	return fig

col_l, col_i, col_e = st.columns(3)
with col_l:
	st.plotly_chart(sunburst_from(out_df, 'ekotehokas_lumo', 'LUMO', total_area=total_area), width='stretch')
	lumo_sum = out_df['ekotehokas_lumo'].sum()
	lumo_norm = round((lumo_sum / total_area) if total_area > 0 else 0, 4)
	st.metric('**Luonnon monimuotisuus -arvo**', value=round(lumo_norm,2))
with col_i:
	if 'ekotehokas_ilm' in out_df.columns:
		st.plotly_chart(sunburst_from(out_df, 'ekotehokas_ilm', 'ILMASTOVIISAUS', total_area=total_area), width='stretch')
		ilm_sum = out_df['ekotehokas_ilm'].sum()
		ilm_norm = round((ilm_sum / total_area) if total_area > 0 else 0, 4)
		st.metric('**Ilmastoviisaus -arvo**', value=round(ilm_norm,2))
	else:
		st.info('Ei ilmastoarvoja (ilm_kp puuttuu)')
with col_e:
	st.plotly_chart(sunburst_from(out_df, 'ekotehokas_hyv', 'HYVINVOINTIHYÖTY', total_area=total_area), width='stretch')
	hyv_sum = out_df['ekotehokas_hyv'].sum()
	hyv_norm = round((hyv_sum / total_area) if total_area > 0 else 0, 4)
	st.metric('**Hyvinvointihyöty -arvo**', value=round(hyv_norm,2))

# with st.expander('Laskennan taulukko (KP-arvot)'):
# 	# human readable column labels
# 	label_map = {
# 		'LUONTOTYYPPI': 'Luontotyyppi',
# 		'kokonaisala': 'Pinta-ala (m2)',
# 		'lumo_kp': 'LUMO kerroin',
# 		'kp_hu': 'Huippuindikaattori (kp_hu)',
# 		'kp_pi': 'Ilmasto - viileys (kp_pi)',
# 		'kp_hi': 'Ilmastosidonta (kp_hi)',
# 		'ilm_kp': 'Ilmastokerroin',
# 		'hy_l_poten': 'Hyvinvointipotentiaali',
# 		'hyvinvo_kp': 'Hyvinvointikerroin',
# 		'ekotehokas_lumo': 'Ekotehokas LUMO',
# 		'ekotehokas_ilm': 'Ekotehokas ILMA',
# 		'ekotehokas_hyv': 'Ekotehokas Hyvinvointi'
# 	}
# 	st.dataframe(out_df.rename(columns=label_map))

