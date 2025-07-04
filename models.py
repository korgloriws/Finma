import threading
import pandas as pd
import yfinance as yf
from flask import Flask
from flask_caching import Cache
import time
import sqlite3
from datetime import datetime
import bcrypt


LISTA_ACOES = [
    
"AALR3.sa",
"ABCB4.sa",
"ABEV3.sa",
"AERI3.sa",
"AFLT3.sa",
"AGRO3.sa",
"AGXY3.sa",
"AHEB5.sa",
"ALLD3.sa",
"ALOS3.sa",
"ALPA3.sa",
"ALPA4.sa",
"ALPK3.sa",
"ALUP11.sa",
"ALUP3.sa",
"ALUP4.sa",
"AMAR11.sa",
"AMAR3.sa",
"AMBP3.sa",
"AMER3.sa",
"AMOB3.sa",
"ANIM3.sa",
"ARML3.sa",
"ASAI3.sa",
"ATED3.sa",
"ATMP3.sa",
"AURE3.sa",
"AVLL3.sa",
"AZEV11.sa",
"AZEV3.sa",
"AZEV4.sa",
"AZTE3.sa",
"AZUL4.sa",
"AZZA3.sa",
"B3SA3.sa",
"BALM3.sa",
"BALM4.sa",
"BAUH4.sa",
"BAZA3.sa",
"BBAS3.sa",
"BBDC3.sa",
"BBDC4.sa",
"BBSE3.sa",
"BDLL3.sa",
"BDLL4.sa",
"BEEF3.sa",
"BEES3.sa",
"BEES4.sa",
"BGIP3.sa",
"BGIP4.sa",
"BHIA3.sa",
"BIED3.sa",
"BIOM3.sa",
"BLAU3.sa",
"BMEB3.sa",
"BMEB4.sa",
"BMGB4.sa",
"BMIN3.sa",
"BMIN4.sa",
"BMKS3.sa",
"BMOB3.sa",
"BNBR3.sa",
"BOBR4.sa",
"BPAC11.sa",
"BPAC3.sa",
"BPAC5.sa",
"BPAN4.sa",
"BRAP3.sa",
"BRAP4.sa",
"BRAV3.sa",
"BRBI11.sa",
"BRFS3.sa",
"BRKM3.sa",
"BRKM5.sa",
"BRKM6.sa",
"BRSR3.sa",
"BRSR5.sa",
"BRSR6.sa",
"BRST3.sa",
"BSLI3.sa",
"BSLI4.sa",
"CAMB3.sa",
"CAML3.sa",
"CASH3.sa",
"CBAV3.sa",
"CBEE3.sa",
"CCTY3.sa",
"CEAB3.sa",
"CEBR3.sa",
"CEBR5.sa",
"CEBR6.sa",
"CEDO4.sa",
"CEEB3.sa",
"CGAS3.sa",
"CGAS5.sa",
"CGRA3.sa",
"CGRA4.sa",
"CLSC3.sa",
"CLSC4.sa",
"CMIG3.sa",
"CMIG4.sa",
"CMIN3.sa",
"COCE3.sa",
"COCE5.sa",
"COGN3.sa",
"CPFE3.sa",
"CPLE3.sa",
"CPLE5.sa",
"CPLE6.sa",
"CRFB3.sa",
"CRPG3.sa",
"CRPG5.sa",
"CRPG6.sa",
"CSAN3.sa",
"CSED3.sa",
"CSMG3.sa",
"CSNA3.sa",
"CSUD3.sa",
"CTKA3.sa",
"CTKA4.sa",
"CTSA3.sa",
"CTSA4.sa",
"CURY3.sa",
"CVCB3.sa",
"CXSE3.sa",
"CYRE3.sa",
"DASA3.sa",
"DESK3.sa",
"DEXP3.sa",
"DEXP4.sa",
"DIRR3.sa",
"DMVF3.sa",
"DOHL3.sa",
"DOHL4.sa",
"DOTZ3.sa",
"DTCY3.sa",
"DXCO3.sa",
"EALT3.sa",
"EALT4.sa",
"ECOR3.sa",
"EGIE3.sa",
"EKTR3.sa",
"EKTR4.sa",
"ELET3.sa",
"ELET6.sa",
"ELMD3.sa",
"EMAE4.sa",
"EMBR3.sa",
"ENEV3.sa",
"ENGI11.sa",
"ENGI3.sa",
"ENGI4.sa",
"ENJU3.sa",
"ENMT3.sa",
"EPAR3.sa",
"EQMA3B.sa",
"EQPA3.sa",
"EQTL3.sa",
"ESPA3.sa",
"ESTR4.sa",
"ETER3.sa",
"EUCA3.sa",
"EUCA4.sa",
"EVEN3.sa",
"EZTC3.sa",
"FESA3.sa",
"FESA4.sa",
"FHER3.sa",
"FICT3.sa",
"FIEI3.sa",
"FIQE3.sa",
"FLRY3.sa",
"FRAS3.sa",
"FRIO3.sa",
"GEPA3.sa",
"GEPA4.sa",
"GFSA3.sa",
"GGBR3.sa",
"GGBR4.sa",
"GGPS3.sa",
"GMAT3.sa",
"GOAU3.sa",
"GOAU4.sa",
"GOLL4.sa",
"GPAR3.sa",
"GRND3.sa",
"GSHP3.sa",
"GUAR3.sa",
"HAGA3.sa",
"HAGA4.sa",
"HAPV3.sa",
"HBOR3.sa",
"HBRE3.sa",
"HBSA3.sa",
"HBTS5.sa",
"HETA4.sa",
"HOOT4.sa",
"HYPE3.sa",
"IFCM3.sa",
"IGTI11.sa",
"IGTI11.sa",
"IGTI3.sa",
"IGTI3.sa",
"INEP3.sa",
"INEP4.sa",
"INTB3.sa",
"IRBR3.sa",
"ISAE3.sa",
"ISAE4.sa",
"ITSA3.sa",
"ITSA4.sa",
"ITUB3.sa",
"ITUB4.sa",
"JALL3.sa",
"JBSS3.sa",
"JFEN3.sa",
"JHSF3.sa",
"JSLG3.sa",
"KEPL3.sa",
"KLBN11.sa",
"KLBN3.sa",
"KLBN4.sa",
"LAND3.sa",
"LAVV3.sa",
"LEVE3.sa",
"LIGT3.sa",
"LIPR3.sa",
"LJQQ3.sa",
"LOGG3.sa",
"LOGN3.sa",
"LPSB3.sa",
"LREN3.sa",
"LUPA3.sa",
"LUXM4.sa",
"LVTC3.sa",
"LWSA3.sa",
"MAPT3.sa",
"MATD3.sa",
"MBLY3.sa",
"MDIA3.sa",
"MDNE3.sa",
"MEAL3.sa",
"MELK3.sa",
"MGEL4.sa",
"MGLU3.sa",
"MILS3.sa",
"MLAS3.sa",
"MNDL3.sa",
"MNPR3.sa",
"MOAR3.sa",
"MOTV3.sa",
"MOVI3.sa",
"MRFG3.sa",
"MRSA3B.sa",
"MRVE3.sa",
"MTRE3.sa",
"MTSA3.sa",
"MTSA4.sa",
"MULT3.sa",
"MWET4.sa",
"MYPK3.sa",
"NEOE3.sa",
"NEXP3.sa",
"NGRD3.sa",
"NORD3.sa",
"NTCO3.sa",
"NUTR3.sa",
"ODPV3.sa",
"OFSA3.sa",
"OIBR3.sa",
"OIBR4.sa",
"ONCO3.sa",
"OPCT3.sa",
"ORVR3.sa",
"OSXB3.sa",
"PATI3.sa",
"PATI4.sa",
"PCAR3.sa",
"PDGR3.sa",
"PDTC3.sa",
"PEAB3.sa",
"PEAB4.sa",
"PETR3.sa",
"PETR4.sa",
"PETZ3.sa",
"PFRM3.sa",
"PGMN3.sa",
"PINE11.sa",
"PINE3.sa",
"PINE4.sa",
"PLAS3.sa",
"PLPL3.sa",
"PMAM3.sa",
"PNVL3.sa",
"POMO3.sa",
"POMO4.sa",
"PORT3.sa",
"POSI3.sa",
"PPLA11.sa",
"PRIO3.sa",
"PRNR3.sa",
"PSSA3.sa",
"PSVM11.sa",
"PTBL3.sa",
"PTNT3.sa",
"PTNT4.sa",
"QUAL3.sa",
"RADL3.sa",
"RAIL3.sa",
"RAIZ4.sa",
"RANI3.sa",
"RAPT3.sa",
"RAPT4.sa",
"RCSL3.sa",
"RCSL4.sa",
"RDNI3.sa",
"RDOR3.sa",
"REAG3.sa",
"RECV3.sa",
"REDE3.sa",
"RENT3.sa",
"RNEW11.sa",
"RNEW3.sa",
"RNEW4.sa",
"ROMI3.sa",
"RPAD3.sa",
"RPAD5.sa",
"RPMG3.sa",
"RSID3.sa",
"RSUL4.sa",
"SANB11.sa",
"SANB3.sa",
"SANB4.sa",
"SAPR11.sa",
"SAPR3.sa",
"SAPR4.sa",
"SBFG3.sa",
"SBSP3.sa",
"SCAR3.sa",
"SEER3.sa",
"SEQL3.sa",
"SHOW3.sa",
"SHUL4.sa",
"SIMH3.sa",
"SLCE3.sa",
"SMFT3.sa",
"SMTO3.sa",
"SNSY3.sa",
"SNSY5.sa",
"SOJA3.sa",
"SOND5.sa",
"SOND6.sa",
"SRNA3.sa",
"STBP3.sa",
"SUZB3.sa",
"SYNE3.sa",
"TAEE11.sa",
"TAEE3.sa",
"TAEE4.sa",
"TASA3.sa",
"TASA4.sa",
"TCSA3.sa",
"TECN3.sa",
"TELB3.sa",
"TELB4.sa",
"TEND3.sa",
"TFCO4.sa",
"TGMA3.sa",
"TIMS3.sa",
"TKNO4.sa",
"TOTS3.sa",
"TPIS3.sa",
"TRAD3.sa",
"TRIS3.sa",
"TTEN3.sa",
"TUPY3.sa",
"UCAS3.sa",
"UGPA3.sa",
"UNIP3.sa",
"UNIP5.sa",
"UNIP6.sa",
"USIM3.sa",
"USIM5.sa",
"USIM6.sa",
"VALE3.sa",
"VAMO3.sa",
"VBBR3.sa",
"VITT3.sa",
"VIVA3.sa",
"VIVR3.sa",
"VIVT3.sa",
"VLID3.sa",
"VSTE3.sa",
"VTRU3.sa",
"VULC3.sa",
"VVEO3.sa",
"WEGE3.sa",
"WEST3.sa",
"WHRL3.sa",
"WHRL4.sa",
"WIZC3.sa",
"WLMM3.sa",
"WLMM4.sa",
"YDUQ3.sa",
"ZAMP3.sa",

    
]
LISTA_FIIS = [
    "ARXD11.SA",
"CCME11.SA",
"ITIT11.SA",
"JASC11.SA",
"AFHI11.SA",
"AJFI11.SA",
"ALZC11.SA",
"ALZM11.SA",
"ALZR11.SA",
"AROA11.SA",
"AIEC11.SA",
"BCRI11.SA",
"BNFS11.SA",
"BTML11.SA",
"BBFO11.SA",
"BBRC11.SA",
"RNDP11.SA",
"BLMG11.SA",
"BCIA11.SA",
"FATN11.SA",
"BRCO11.SA",
"BICE11.SA",
"BIME11.SA",
"BRIM11.SA",
"BRIP11.SA",
"BIPD11.SA",
"BROF11.SA",
"LLAO11.SA",
"BTHI11.SA",
"BTLG11.SA",
"BTWR11.SA",
"BTSG11.SA",
"BTSI11.SA",
"CRFF11.SA",
"CXRI11.SA",
"CPOF11.SA",
"CPFF11.SA",
"CPTS11.SA",
"CPSH11.SA",
"CACR11.SA",
"CBOP11.SA",
"BLCA11.SA",
"CFHI11.SA",
"CFII11.SA",
"CJCT11.SA",
"CLIN11.SA",
"HGFF11.SA",
"HGLG11.SA",
"HGPO11.SA",
"HGRE11.SA",
"HGCR11.SA",
"HGRU11.SA",
"CYCR11.SA",
"DPRO11.SA",
"DEVA11.SA",
"EQIR11.SA",
"ERPA11.SA",
"KEVE11.SA",
"EXES11.SA",
"FLCR11.SA",
"VRTA11.SA",
"VRTM11.SA",
"MMPD11.SA",
"IBCR11.SA",
"IDGR11.SA",
"GAME11.SA",
"TRBL11.SA",
"FAED11.SA",
"BMLC11.SA",
"BPRP11.SA",
"BRCR11.SA",
"BTHF11.SA",
"FCFL11.SA",
"CNES11.SA",
"CEOC11.SA",
"EDGA11.SA",
"HCRI11.SA",
"NSLU11.SA",
"HTMX11.SA",
"MAXR11.SA",
"NCHB11.SA",
"NVHO11.SA",
"PQDP11.SA",
"RBRR11.SA",
"RECR11.SA",
"RECT11.SA",
"TRNT11.SA",
"OUFF11.SA",
"LVBI11.SA",
"BPFF11.SA",
"BVAR11.SA",
"BPML11.SA",
"BTRA11.SA",
"CXCI11.SA",
"CXCE11.SA",
"CXTL11.SA",
"FLMA11.SA",
"EURO11.SA",
"ABCP11.SA",
"GTWR11.SA",
"HUCG11.SA",
"HUSC11.SA",
"FIIB11.SA",
"FMOF11.SA",
"OULG11.SA",
"FPNG11.SA",
"FPAB11.SA",
"RBRY11.SA",
"RBRP11.SA",
"RCRB11.SA",
"RBED11.SA",
"RBVA11.SA",
"RNGO11.SA",
"FISC11.SA",
"SCPF11.SA",
"SHPH11.SA",
"TGAR11.SA",
"BARI11.SA",
"VERE11.SA",
"FVPQ11.SA",
"VTLT11.SA",
"VSHO11.SA",
"IDFI11.SA",
"PLCR11.SA",
"RELG11.SA",
"CVBI11.SA",
"MCCI11.SA",
"ARRI11.SA",
"BTAL11.SA",
"CXCO11.SA",
"HOSI11.SA",
"MGHT11.SA",
"RECX11.SA",
"PVBI11.SA",
"DVFF11.SA",
"RFOF11.SA",
"VVMR11.SA",
"BTCI11.SA",
"IRDM11.SA",
"GARE11.SA",
"KFOF11.SA",
"OURE11.SA",
"SNEL11.SA",
"BLUR11.SA",
"SPXS11.SA",
"APXM11.SA",
"BRLA11.SA",
"CXAG11.SA",
"HBCR11.SA",
"MINT11.SA",
"RZTR11.SA",
"ROOF11.SA",
"GCRI11.SA",
"GCOI11.SA",
"GZIT11.SA",
"FIGS11.SA",
"GLOG11.SA",
"GGRC11.SA",
"HABT11.SA",
"CPUR11.SA",
"HCTR11.SA",
"HCHG11.SA",
"HAAA11.SA",
"HGBL11.SA",
"HGBS11.SA",
"HDEL11.SA",
"FLRP11.SA",
"HLOG11.SA",
"HOFC11.SA",
"HREC11.SA",
"SEED11.SA",
"HPDP11.SA",
"HFOF11.SA",
"HGIC11.SA",
"HSAF11.SA",
"HSLG11.SA",
"HSML11.SA",
"HSRE11.SA",
"HUSI11.SA",
"ITIP11.SA",
"BICR11.SA",
"IRIM11.SA",
"ICRI11.SA",
"TMPS11.SA",
"ITRI11.SA",
"JBFO11.SA",
"JFLL11.SA",
"JCCJ11.SA",
"JPPA11.SA",
"JSAF11.SA",
"JSRE11.SA",
"KISU11.SA",
"KIVO11.SA",
"KCRE11.SA",
"KNHF11.SA",
"KNHY11.SA",
"KNIP11.SA",
"KORE11.SA",
"KNRI11.SA",
"KNCR11.SA",
"KNSC11.SA",
"KNUQ11.SA",
"LPLP11.SA",
"LASC11.SA",
"LSPA11.SA",
"LIFE11.SA",
"LFTT11.SA",
"LGCP11.SA",
"LUGG11.SA",
"MALL11.SA",
"MANA11.SA",
"MCHF11.SA",
"MCHY11.SA",
"MXRF11.SA",
"MFII11.SA",
"MFAI11.SA",
"MFCR11.SA",
"MORE11.SA",
"MORC11.SA",
"NCRI11.SA",
"NAVT11.SA",
"APTO11.SA",
"NEWL11.SA",
"NEWU11.SA",
"OCRE11.SA",
"OUJP11.SA",
"PNCR11.SA",
"PNDL11.SA",
"PNPR11.SA",
"PNRC11.SA",
"PMIS11.SA",
"PQAG11.SA",
"PATC11.SA",
"PATL11.SA",
"PEMA11.SA",
"PORD11.SA",
"PLRI11.SA",
"QAGR11.SA",
"RSPD11.SA",
"RBIR11.SA",
"RBLG11.SA",
"RRCI11.SA",
"RBRD11.SA",
"RBTS11.SA",
"RBRF11.SA",
"RCFF11.SA",
"RBRL11.SA",
"RBRX11.SA",
"RPRI11.SA",
"RMAI11.SA",
"RINV11.SA",
"RBHG11.SA",
"RBHY11.SA",
"RBVO11.SA",
"RBFF11.SA",
"RBOP11.SA",
"RBRS11.SA",
"RZAK11.SA",
"SADI11.SA",
"SAPI11.SA",
"SARE11.SA",
"SEQR11.SA",
"WPLZ11.SA",
"REIT11.SA",
"SPTW11.SA",
"PMFO11.SA",
"STRX11.SA",
"SNFF11.SA",
"SNLG11.SA",
"SNME11.SA",
"SNCI11.SA",
"TEPP11.SA",
"TSER11.SA",
"TVRI11.SA",
"TJKB11.SA",
"TSNC11.SA",
"TRXF11.SA",
"TRXB11.SA",
"URPR11.SA",
"VVCR11.SA",
"VVRI11.SA",
"VGIR11.SA",
"VGIP11.SA",
"VGII11.SA",
"VGHF11.SA",
"VGRI11.SA",
"BLMC11.SA",
"BLMO11.SA",
"RVBI11.SA",
"BLMR11.SA",
"FLFL11.SA",
"VCJR11.SA",
"VCRR11.SA",
"VSLH11.SA",
"VCRI11.SA",
"VIUR11.SA",
"VIFI11.SA",
"VILG11.SA",
"VINO11.SA",
"VISC11.SA",
"VOTS11.SA",
"WSEC11.SA",
"WHGR11.SA",
"XPCM11.SA",
"XPCI11.SA",
"XPIN11.SA",
"XPLG11.SA",
"XPML11.SA",
"XPPR11.SA",
"XPSF11.SA",
"YUFI11.SA",
"ZAGH11.SA",
"ZAVC11.SA",
"ZAVI11.SA",
]
LISTA_BDRS = [
    "ABUD34.SA",
"ABTT34.SA",
"ABBV34.SA",
"A1AP34.SA",
"A1EG34.SA",
"A1ES34.SA",
"A1FL34.SA",
"A1GI34.SA",
"A1PD34.SA",
"A1LB34.SA",
"A1RE34.SA",
"BABA34.SA",
"A1GN34.SA",
"A1LL34.SA",
"A1EN34.SA",
"A1TT34.SA",
"MOOO34.SA",
"A1CR34.SA",
"A1EE34.SA",
"A1EP34.SA",
"T1OW34.SA",
"A1WK34.SA",
"A1MP34.SA",
"A1ME34.SA",
"AMGN34.SA",
"A1PH34.SA",
"A1DI34.SA",
"A1OS34.SA",
"A1ON34.SA",
"A1PA34.SA",
"AAPL34.SA",
"A1MT34.SA",
"ARMT34.SA",
"A1DM34.SA",
"AWII34.SA",
"A1JG34.SA",
"ASML34.SA",
"A1SU34.SA",
"A1ZN34.SA",
"A1TM34.SA",
"A1TH34.SA",
"ADPR34.SA",
"A1VB34.SA",
"A1VY34.SA",
"B1KR34.SA",
"B1LL34.SA",
"B1SA34.SA",
"BOAC34.SA",
"B1CS34.SA",
"B1AX34.SA",
"B1BT34.SA",
"B1DX34.SA",
"BBYY34.SA",
"BILB34.SA",
"T1CH34.SA",
"BLAK34.SA",
"BKNG34.SA",
"B1WA34.SA",
"BOXP34.SA",
"B1PP34.SA",
"B1TI34.SA",
"AVGO34.SA",
"B1RF34.SA",
"B1AM34.SA",
"B1FC34.SA",
"C1AB34.SA",
"C1OG34.SA",
"C1PB34.SA",
"C2PT34.SA",
"CNIC34.SA",
"CPRL34.SA",
"CAON34.SA",
"C1AH34.SA",
"C1RR34.SA",
"CRIN34.SA",
"C1BO34.SA",
"C1BS34.SA",
"C1DW34.SA",
"C1NS34.SA",
"C1NP34.SA",
"C1FI34.SA",
"C1HR34.SA",
"C1BL34.SA",
"C1HT34.SA",
"CHDC34.SA",
"C1IC34.SA",
"CINF34.SA",
"C1TA34.SA",
"CSCO34.SA",
"CTGP34.SA",
"C1FG34.SA",
"CLXC34.SA",
"CHME34.SA",
"C1MS34.SA",
"CTSH34.SA",
"CMCS34.SA",
"C1MA34.SA",
"C1AG34.SA",
"E1DI34.SA",
"STZB34.SA",
"C1OO34.SA",
"COPH34.SA",
"G1LW34.SA",
"C1TV34.SA",
"COWC34.SA",
"C1CI34.SA",
"CSXC34.SA",
"C1MI34.SA",
"CVSH34.SA",
"DHER34.SA",
"D1RI34.SA",
"DEEC34.SA",
"D1EL34.SA",
"DEAI34.SA",
"XRAY34.SA",
"DBAG34.SA",
"D1VN34.SA",
"DEOP34.SA",
"F1AN34.SA",
"D1LR34.SA",
"D1FS34.SA",
"DGCO34.SA",
"D1OM34.SA",
"D2PZ34.SA",
"D1OV34.SA",
"D1OW34.SA",
"D1HI34.SA",
"R1DY34.SA",
"D1TE34.SA",
"E1MN34.SA",
"E1TN34.SA",
"EBAY34.SA",
"E1CL34.SA",
"E1CO34.SA",
"E1IX34.SA",
"EAIN34.SA",
"E1MR34.SA",
"E1TR34.SA",
"E1OG34.SA",
"EQIX34.SA",
"E1QN34.SA",
"E1QR34.SA",
"E1RI34.SA",
"E1SS34.SA",
"ELCI34.SA",
"E1VE34.SA",
"E1VR34.SA",
"E1SE34.SA",
"E1XP34.SA",
"E1XR34.SA",
"EXXO34.SA",
"FASL34.SA",
"F1NI34.SA",
"FFTD34.SA",
"F1EC34.SA",
"F1LS34.SA",
"F1MC34.SA",
"FDMO34.SA",
"F1TV34.SA",
"F1BH34.SA",
"FOXC34.SA",
"F2NV34.SA",
"F1RA34.SA",
"FCXO34.SA",
"FMSC34.SA",
"GPSI34.SA",
"G1RM34.SA",
"GEOO34.SA",
"G1MI34.SA",
"GMCO34.SA",
"G1PC34.SA",
"GPRK34.SA",
"GILD34.SA",
"G1SK34.SA",
"G1PI34.SA",
"G1LL34.SA",
"G1FI34.SA",
"GSGI34.SA",
"H1RB34.SA",
"HALI34.SA",
"THGI34.SA",
"H1OG34.SA",
"H1IG34.SA",
"H1AS34.SA",
"H1CA34.SA",
"H1DB34.SA",
"P1EA34.SA",
"H1EI34.SA",
"HSHY34.SA",
"H1ES34.SA",
"H1PE34.SA",
"H1LT34.SA",
"H1FC34.SA",
"HOME34.SA",
"HOND34.SA",
"H1RL34.SA",
"H1ST34.SA",
"ARNC34.SA",
"H1SB34.SA",
"H1TH34.SA",
"H1UM34.SA",
"H1BA34.SA",
"H1II34.SA",
"I1BN34.SA",
"I1EX34.SA",
"I1TW34.SA",
"I1FO34.SA",
"I1RP34.SA",
"ITLC34.SA",
"I1CE34.SA",
"I1HG34.SA",
"I1PC34.SA",
"I1FF34.SA",
"I1PH34.SA",
"INTU34.SA",
"I1VZ34.SA",
"I1RM34.SA",
"J1KH34.SA",
"J1EG34.SA",
"J1BH34.SA",
"JDCO34.SA",
"J1EF34.SA",
"J1CI34.SA",
"JPMC34.SA",
"J1NP34.SA",
"K1BF34.SA",
"K1EL34.SA",
"KMPR34.SA",
"K1EY34.SA",
"K1IM34.SA",
"KMIC34.SA",
"K1LA34.SA",
"K1SS34.SA",
"PHGN34.SA",
"K1RC34.SA",
"K1TC34.SA",
"L1HX34.SA",
"L1CA34.SA",
"L1RC34.SA",
"L1WH34.SA",
"L1VS34.SA",
"L1EG34.SA",
"L1DO34.SA",
"L1EN34.SA",
"LILY34.SA",
"L1NC34.SA",
"L1KQ34.SA",
"L1YG34.SA",
"L1OE34.SA",
"LOWC34.SA",
"L1YB34.SA",
"M1TB34.SA",
"MACY34.SA",
"M1RO34.SA",
"M1PC34.SA",
"M1KT34.SA",
"M1TT34.SA",
"M1MC34.SA",
"M1LM34.SA",
"M1AS34.SA",
"M1KC34.SA",
"MCDC34.SA",
"M1CK34.SA",
"MDTC34.SA",
"MRCK34.SA",
"M1CH34.SA",
"MUTC34.SA",
"MSFT34.SA",
"M1AA34.SA",
"M1UF34.SA",
"M1CB34.SA",
"MDLZ34.SA",
"MCOR34.SA",
"MOSC34.SA",
"M1SI34.SA",
"M1SC34.SA",
"N1DA34.SA",
"N1GG34.SA",
"N1OV34.SA",
"N1WG34.SA",
"N1TA34.SA",
"NETE34.SA",
"N1WL34.SA",
"N1EM34.SA",
"N1WS34.SA",
"N1WS35.SA",
"NEXT34.SA",
"N1IS34.SA",
"NOKI34.SA",
"NMRH34.SA",
"J1WN34.SA",
"N1SC34.SA",
"N1TR34.SA",
"NOCG34.SA",
"N1VS34.SA",
"N1VO34.SA",
"N1RG34.SA",
"N1UE34.SA",
"NVDC34.SA",
"N1XP34.SA",
"OXYP34.SA",
"O1DF34.SA",
"O1MC34.SA",
"O1KE34.SA",
"I1XC34.SA",
"O1TI34.SA",
"P1AC34.SA",
"P1KG34.SA",
"P1HC34.SA",
"P1AY34.SA",
"P1YC34.SA",
"P1NR34.SA",
"P1RG34.SA",
"PFIZ34.SA",
"PGCO34.SA",
"PHMO34.SA",
"P1SX34.SA",
"P1NW34.SA",
"P1IO34.SA",
"PNCS34.SA",
"P1KX34.SA",
"P1PG34.SA",
"P1PL34.SA",
"P1FG34.SA",
"P1LD34.SA",
"P1DT34.SA",
"P1UK34.SA",
"T1LK34.SA",
"P1EG34.SA",
"P1SA34.SA",
"P1HM34.SA",
"P1VH34.SA",
"QCOM34.SA",
"Q1UA34.SA",
"Q1UE34.SA",
"R1LC34.SA",
"R1JF34.SA",
"R1IN34.SA",
"R1EG34.SA",
"R1FC34.SA",
"R1EL34.SA",
"R1SG34.SA",
"R1MD34.SA",
"RIOT34.SA",
"R1HI34.SA",
"R1OK34.SA",
"R1OL34.SA",
"R1OP34.SA",
"ROST34.SA",
"R1YA34.SA",
"SPGI34.SA",
"SSFO34.SA",
"BCSA34.SA",
"SAPP34.SA",
"S1BA34.SA",
"SCHW34.SA",
"S1TX34.SA",
"S1EA34.SA",
"S1RE34.SA",
"S1BS34.SA",
"SIMN34.SA",
"SRXM34.SA",
"S1KM34.SA",
"S1SL34.SA",
"S1LG34.SA",
"S1NN34.SA",
"S1NA34.SA",
"SNEC34.SA",
"S1OU34.SA",
"S1SN34.SA",
"S1WK34.SA",
"S1TT34.SA",
"S1TE34.SA",
"STMN34.SA",
"S1YK34.SA",
"S1MF34.SA",
"S1YM34.SA",
"S1YF34.SA",
"S1YY34.SA",
"T1RO34.SA",
"TSMC34.SA",
"TAKP34.SA",
"TPRY34.SA",
"T1EL34.SA",
"T1EC34.SA",
"T1FX34.SA",
"TLNC34.SA",
"T2PX34.SA",
"T1SS34.SA",
"TXSA34.SA",
"T1XT34.SA",
"S1JM34.SA",
"P1GR34.SA",
"S1HW34.SA",
"T1SO34.SA",
"TMOS34.SA",
"TJXC34.SA",
"T1MU34.SA",
"TMCO34.SA",
"T1SC34.SA",
"T1DG34.SA",
"TRVC34.SA",
"TSNF34.SA",
"UBSG34.SA",
"U1DR34.SA",
"ULEV34.SA",
"UPAC34.SA",
"U1RI34.SA",
"UNHH34.SA",
"U1HS34.SA",
"U1NM34.SA",
"UPSS34.SA",
"USSX34.SA",
"VLOE34.SA",
"VLYB34.SA",
"V1TA34.SA",
"V1RS34.SA",
"VERZ34.SA",
"VFCO34.SA",
"V1IP34.SA",
"V1OD34.SA",
"V1NO34.SA",
"V1MC34.SA",
"W1AB34.SA",
"WALM34.SA",
"WGBA34.SA",
"W1MG34.SA",
"W1MC34.SA",
"W1SO34.SA",
"W1EC34.SA",
"W1BO34.SA",
"WFCO34.SA",
"W1EL34.SA",
"W2ST34.SA",
"WABC34.SA",
"WUNI34.SA",
"W1YC34.SA",
"W1HR34.SA",
"W1MB34.SA",
"W1LT34.SA",
"W1PP34.SA",
"W1RB34.SA",
"G1WW34.SA",
"W1YN34.SA",
"X1EL34.SA",
"X1YL34.SA",
"YUMR34.SA",
"Z1BH34.SA",
"Z1IO34.SA",
"Z1TS34.SA",
"Z1TO34.SA",
"ACNB34.SA",
"AIGB34.SA",
"AXPB34.SA",
"ATTB34.SA",
"BONY34.SA",
"BMYB34.SA",
"DUKB34.SA",
"DDNB34.SA",
"FDXB34.SA",
"FMXB34.SA",
"GDBR34.SA",
"HONB34.SA",
"HPQB34.SA",
"IBMB34.SA",
"JNJB34.SA",
"KMBB34.SA",
"KHCB34.SA",
"LMTB34.SA",
"METB34.SA",
"MSBR34.SA",
"PEPB34.SA",
"SBUB34.SA",
"TGTB34.SA",
"TEXA34.SA",
"VISA34.SA",
"DISB34.SA",
"XRXB34.SA",
"CATP34.SA",
"CHVX34.SA",
"COCA34.SA",
"COLG34.SA",
"MSCD34.SA",
"NIKE34.SA",
"ORCL34.SA",
"RYTT34.SA",
"SLBG34.SA",
"USBC34.SA",
"XPBR31.SA",
"STLA",
"TLK",
]

df_ativos = None
carregamento_em_andamento = False
lock = threading.Lock()  


cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})


import threading
import pandas as pd
import yfinance as yf

global_state = {"df_ativos": None, "carregando": False}

def carregar_ativos():
    acoes = LISTA_ACOES
    fiis = LISTA_FIIS
    bdrs = LISTA_BDRS
    
    try:
        print("🔄 Iniciando carregamento de ativos...")
        


        acoes_filtradas = processar_ativos(acoes, 'Ação')
        bdrs_filtradas = processar_ativos(bdrs, 'BDR')
        fiis_filtradas = processar_ativos(fiis, 'FII')



        ativos_filtrados = acoes_filtradas + bdrs_filtradas + fiis_filtradas

        if not ativos_filtrados:
            print(" Nenhum ativo foi carregado. Algo deu errado!")
            return

        df_ativos = pd.DataFrame(ativos_filtrados)
        
        if df_ativos.empty:
            print(" O DataFrame gerado está vazio! Verifique os filtros.")
        else:
            print(f" Carregamento concluído! {len(df_ativos)} ativos carregados.")
            print(f" Colunas disponíveis: {df_ativos.columns.tolist()}")

        global_state["df_ativos"] = df_ativos

    except Exception as e:
        print(f" Erro no carregamento dos ativos: {e}")







def obter_informacoes(ticker, tipo_ativo, max_retentativas=3):
    def to_float_or_inf(valor):

        try:
            return float(valor)
        except (ValueError, TypeError):
            return float('inf')

    tentativas = 0
    while tentativas < max_retentativas:
        try:
            print(f"🔍 Buscando informações para {ticker}...")

            acao = yf.Ticker(ticker)
            info = acao.info


            if not info or "sector" not in info:
                print(f" Ativo {ticker} não encontrado na API do Yahoo Finance. Ignorando...")
                return None


            preco_atual = info.get("currentPrice", 0.0)
            roe_raw = info.get("returnOnEquity", 0.0)
            dividend_yield_api = info.get("dividendYield", 0.0)
            average_volume = info.get("averageVolume", 0)  
            liquidez_diaria = preco_atual * average_volume


            trailing_pe_raw = info.get("trailingPE", float('inf'))
            price_to_book_raw = info.get("priceToBook", float('inf'))

            pl = to_float_or_inf(trailing_pe_raw)
            pvp = to_float_or_inf(price_to_book_raw)

       
            roe = round(roe_raw * 100, 2) if roe_raw else 0.0
            dividend_yield = round(dividend_yield_api, 6)
            setor = info.get("sector", "").strip() or "Desconhecido"

            return {
                "ticker": ticker,
                "nome_completo": info.get("longName", ""),
                "setor": setor,
                "industria": info.get("industry", ""),
                "website": info.get("website", ""),
                "roe": roe,
                "preco_atual": preco_atual,
                "dividend_yield": dividend_yield,
                "pl": pl,
                "pvp": pvp,
                "pais": info.get("country", ""),
                "tipo": tipo_ativo,
                "liquidez_diaria": liquidez_diaria,
                "volume_medio": average_volume,
            }

        except Exception as e:
            msg_erro = str(e).lower()
            if "too many requests" in msg_erro or "rate limited" in msg_erro:
                print(f"⚠️ Rate limit detectado para {ticker}. Aguardando 60s e tentando novamente...")
                time.sleep(60)
                tentativas += 1
            else:
                print(f" Erro ao obter informações para {ticker}: {e}")
                return None

    print(f"⚠️ Não foi possível obter {ticker} após {max_retentativas} tentativas. Ignorando...")
    return None







def aplicar_filtros_acoes(dados):

    return sorted([
        ativo for ativo in dados if (
            ativo['roe'] >= 10 and
            ativo['dividend_yield'] > 15 and
            1 <= ativo['pl'] <= 10 and
            ativo['pvp'] <= 2
        )
    ], key=lambda x: x['dividend_yield'], reverse=True)[:10]


def aplicar_filtros_bdrs(dados):

    return sorted([
        ativo for ativo in dados if (
            ativo['roe'] >= 10 and
            ativo['dividend_yield'] > 3 and
            1 <= ativo['pl'] <= 10 and
            ativo['pvp'] <= 3
        )
    ], key=lambda x: x['dividend_yield'], reverse=True)[:10]


def aplicar_filtros_fiis(dados):
    return sorted([
        ativo for ativo in dados if (
            10 <= ativo['dividend_yield'] <= 12 and
            ativo.get("liquidez_diaria", 0) > 1000_000
        )
    ], key=lambda x: x['dividend_yield'], reverse=True)[:10]



def processar_ativos(lista, tipo):

    dados = [obter_informacoes(ticker, tipo) for ticker in lista]
    dados = [d for d in dados if d is not None] 

    print(f"🔍 {tipo}: {len(dados)} ativos recuperados antes dos filtros.")

    if not dados:
        print(f" Nenhum ativo válido foi encontrado para {tipo}. Verifique a API.")
        return []

    ativos_filtrados = (
        aplicar_filtros_acoes(dados) if tipo == 'Ação' else
        aplicar_filtros_bdrs(dados) if tipo == 'BDR' else
        aplicar_filtros_fiis(dados) if tipo == 'FII' else
        []
    )


    ativos_rejeitados = set(d['ticker'] for d in dados) - set(d['ticker'] for d in ativos_filtrados)
    print(f" {len(ativos_rejeitados)} {tipo}s foram rejeitados pelos filtros: {ativos_rejeitados}")

    print(f" {len(ativos_filtrados)} {tipo}s passaram nos filtros.")
    return ativos_filtrados



def formatar_dados(ativos):

    for ativo in ativos:
        ativo['preco_atual_display'] = formatar_numero(ativo.get('preco_atual', 0), 'preco')
        ativo['roe_display'] = formatar_numero(ativo.get('roe', 0), 'percentual')
        if ativo["dividend_yield"] is not None:
            ativo["dividend_yield_display"] = f"{ativo['dividend_yield'] * 100:.2f}%".replace(".", ",")
        else:
            ativo["dividend_yield_display"] = "N/A"  


    return ativos


def formatar_numero(numero, tipo='preco'):

    if tipo == 'preco':
        return f'R$ {numero:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    elif tipo == 'percentual':
        return f'{numero:.2f}%'.replace('.', ',')
    return numero







def obter_todas_informacoes(ticker):
    try:
        acao = yf.Ticker(ticker)
        print(f"Obtendo informações brutas para {ticker}...")
        info = acao.info
        historico = acao.history(period="max")

        return {
            "info": info if info else {},
            "historico": historico,
            "dividends": acao.dividends,
            "splits": acao.splits,
            "recomendacoes": acao.recommendations,
            "sustainability": acao.sustainability,
            "holders": acao.major_holders,
            "earnings": acao.earnings,
            "quarterly_earnings": acao.quarterly_earnings,
            "balance_sheet": acao.balance_sheet,
            "cashflow": acao.cashflow,
            "quarterly_balance_sheet": acao.quarterly_balance_sheet,
            "quarterly_cashflow": acao.quarterly_cashflow,
            "financials": acao.financials,
            "quarterly_financials": acao.quarterly_financials
        }
    except Exception as e:
        print(f"Erro ao obter informações para {ticker}: {e}")
        return None



USUARIOS_DB_PATH = 'usuarios.db'

def criar_tabela_usuarios():
    conn = sqlite3.connect(USUARIOS_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            data_cadastro TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def cadastrar_usuario(nome, username, senha):
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    data_cadastro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(USUARIOS_DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO usuarios (nome, username, senha_hash, data_cadastro) VALUES (?, ?, ?, ?)''',
                  (nome, username, senha_hash, data_cadastro))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def buscar_usuario_por_username(username):
    conn = sqlite3.connect(USUARIOS_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, nome, username, senha_hash, data_cadastro FROM usuarios WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'nome': row[1],
            'username': row[2],
            'senha_hash': row[3],
            'data_cadastro': row[4]
        }
    return None

def verificar_senha(username, senha):
    usuario = buscar_usuario_por_username(username)
    if usuario:
        return bcrypt.checkpw(senha.encode('utf-8'), usuario['senha_hash'].encode('utf-8'))
    return False

def processar_ativos_acoes_com_filtros(roe_min, dy_min, pl_min, pl_max, pvp_max):
    acoes = LISTA_ACOES
    dados = [obter_informacoes(ticker, 'Ação') for ticker in acoes]
    dados = [d for d in dados if d is not None]
    filtrados = [
        ativo for ativo in dados if (
            ativo['roe'] >= (roe_min or 0) and
            ativo['dividend_yield'] > (dy_min or 0) and
            (pl_min or 0) <= ativo['pl'] <= (pl_max or float('inf')) and
            ativo['pvp'] <= (pvp_max or float('inf'))
        )
    ]
    return sorted(filtrados, key=lambda x: x['dividend_yield'], reverse=True)[:10]

def processar_ativos_bdrs_com_filtros(roe_min, dy_min, pl_min, pl_max, pvp_max):
    bdrs = LISTA_BDRS
    dados = [obter_informacoes(ticker, 'BDR') for ticker in bdrs]
    dados = [d for d in dados if d is not None]
    filtrados = [
        ativo for ativo in dados if (
            ativo['roe'] >= (roe_min or 0) and
            ativo['dividend_yield'] > (dy_min or 0) and
            (pl_min or 0) <= ativo['pl'] <= (pl_max or float('inf')) and
            ativo['pvp'] <= (pvp_max or float('inf'))
        )
    ]
    return sorted(filtrados, key=lambda x: x['dividend_yield'], reverse=True)[:10]

def processar_ativos_fiis_com_filtros(dy_min, dy_max, liq_min):
    fiis = LISTA_FIIS
    dados = [obter_informacoes(ticker, 'FII') for ticker in fiis]
    dados = [d for d in dados if d is not None]
    filtrados = [
        ativo for ativo in dados if (
            (dy_min or 0) <= ativo['dividend_yield'] <= (dy_max or float('inf')) and
            ativo.get('liquidez_diaria', 0) > (liq_min or 0)
        )
    ]
    return sorted(filtrados, key=lambda x: x['dividend_yield'], reverse=True)[:10]





