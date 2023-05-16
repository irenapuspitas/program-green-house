# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 12:56:12 2021
REVISI TERAKHIR; 16/11/2021

PERHITUNGAN EVAPORATIVE COOLING DENGAN BERDASARKAN
PADA LIBRARY UDARA LEMBAB PSYPY

Komponen:
    - kipas exhaust
    - sistem fogging (pompa + nozzle)

Misalkan udara pada t1 dan rh1 ingin diubah menjadi t2 dan rh2.
Untuk mencapai hal itu, ada dua pendekatan yaitu perhitungan yang didasarkan
pada suhu bola kering yang ingin dicapai (t2) atau kelembaban relatif yang 
ingin dicapai. 

perhitungan berdasarkan suhu bola kering --> itung_fogging_suhu()
perhitungan berdasarkan rh  --> hitung_fogging_rh()

waktu fogging (tf)
- output dalam detik
- koreksi untuk lama waktu fogging minimal: 120 detik
- ada koreksi untuk waktu maksimal: 420 detik
- pembulatan ke 5 angka terdekat
@author: muhaemin
"""

import math
from psypy import psySI as SI

# ukuran utama GH
GH_ELEV = 770 # elevasi GH yang digunakan
GH_PANJANG = 25
GH_LEBAR = 15
GH_TINGGI_1 = 3
GH_TINGGI_2 = 4

# kipas
KIPAS_DEBIT = 65
KIPAS_JML = 7

# sistem fogging
NOZZLE_DEBIT = 0.2
NOZZLE_JML_PER_GRUP = 12
NOZZLE_JML_GRUP = 6
DURASI_FOGGING_MIN = 120 # detik
DURASI_FOGGING_MAX = 600 #480 # detik
KOEF_EVAPORASI = 0.8 # persentase fog yang menguap

# koefisien Tdb ketika tdb target terlalu rendah
KOEF_TDB = 1/3

# definisi fungsi
def bulatkan_5terdekat(n0):
    # membulatkan bilangan bulat ke kelipatan angka 5 terdekat
    # seperti 5 dan 10
    # misalkan:
    # 33 --> 35
    # 37 --> 40
    
    # membaca digit terakhir
    n_ = n0 % 10
    
    # menentukan pembulatan ke kelipatan 5 terdekat
    if n_ ==0:
        nt = 0
    elif n_<=5:
        nt = 5
    else:
        nt = 10

    # potong digit terakhir, ambil bagian depan
    n1 = n0//10 # hasil potongan bagian depan
    n2 = n1 * 10 # kalikan 10
    
    # gabungkan kembali potongan depan dan hasil pembulatan
    n3 = n2 + nt
    return n3

def tKelvin(t):
    # konversi Celcius ke Kelvin
    k=t+273.15
    return k

def tCelsius(K):
    # konversi dari Kelvin ke Celcius
    c=K-273.15
    return c

def massa_jenis_u(p,t):      
    # menghitung massa jenis udara lembab
    # p: tekanan udara (Pa)
    # t: suhu bola kering (C)
    
    RUK = 287.058 # konstanta gas utk udara lembab
    T=tKelvin(t)
    r=p/(RUK*T)
    return r

def tekanan_u(t,elev=GH_ELEV):        
    # tekanan udara pada elevasi dan suhu tertentu
    # elev: elevasi tempat (m)
    # t: suhu bola kering (C)
    # t1, rh1: kondisi awal
    # t2, rh2: kondisi akhir yang diinginkan
    
    P0=101325 # tekanan pada permukaan laut (elevasi = 0)
    T=tKelvin(t)
    p=P0*math.e**(-0.02896*9.807*elev/(8.3143*T))
    return p

def volume_u(panjang=GH_PANJANG, lebar=GH_LEBAR, tinggi_1=GH_TINGGI_1, tinggi_2=GH_TINGGI_2):
    # menghitung volume udara dalam GH
    # ukuran disajikan sebagai konstanta.
    # Volume udara dihitung dalam 2 bagian besar untuk
    # memudahkan bila diperlukan massa udara dalam ruang utama
    # dan massa udara dalam bagian atap saja.
    # input
    # panjang, lebar : ukuran GH
    # tinggi_1: tinggi ruang utama
    # tinggi_2: tinggi atap (di atas ruang utama)
    # output:
    # vu_u: volume ruang utama GH yang digunakan utk budidaya tanaman
    # vu_a: volume ruangan di bawah atap dan di atas ruangan pertama
    # vu_total: jumlah keseluruhan volume
    # 
    
    vu_u = panjang * lebar * tinggi_1
    vu_a = 1/2 * lebar * tinggi_2 * panjang
    vu_total = vu_u + vu_a
    return vu_u, vu_a, vu_total

def kipas_lama_nyala(debit=KIPAS_DEBIT,jumlah=KIPAS_JML):
    # menghitung lama nyala kipas dengan berdasarkan pada
    # debit: debit 1 kipas
    # jumlah: jumlah kipas
    
    qis = debit/60 # m3/detik
    _,_,vu_total = volume_u() # volume udara dalam GH
    q_total= debit/60 * jumlah # m3/detik
    wk = vu_total/q_total # lama nyala dlm detik
    return wk

def debit_sistem_fogging(debit_tiap_nozle=NOZZLE_DEBIT, nozle_per_grup=NOZZLE_JML_PER_GRUP,jml_grup=NOZZLE_JML_GRUP):
    # menghitung debit sistem fogging (gram air/detik)
    # dari kapasitas tiap nozzle dan jumlah nozzle
    # n_debit : debit
    qzg = debit_tiap_nozle * nozle_per_grup # debit/grup atau debit/pompa
    q_total= qzg * jml_grup
    return q_total

def hitung_fogging_suhu(t1,rh1,t2, kTdb=KOEF_TDB, kEvap=KOEF_EVAPORASI,dMin=DURASI_FOGGING_MIN,dMax=DURASI_FOGGING_MAX):
    # menghitung lama waktu penyalaan sistem
    # fogging dengan berdasarkan pada 
    # perhitungan suhu bola kering akhir
    # t1, rh1: suhu dan RH awal
    # t2, rh2: suhu dan RH akhir/target yang diinginkan
    # Twb:  suhu bola basah
    # kTdb: koefisien penambahan nilai tdb dari twb ketika tdb target
    #       terlalu rendah dan harus direvisi
    
    tpesan='-'
    
    # kondisi 1 (awal, sekarang)
    T1 = tKelvin(t1)
    p1 = tekanan_u(t1) # tekanan udara
    rh1 = rh1/100
    
    # menghitung TWB, w1 dan V
    _,_,_,V,w1,TWB1 = SI.state("DBT",T1,"RH",rh1,p1)
    # TWB = HAPropsSI('B','T',T1,'P',p1,'R',rh1) # dalam Kelvin
    twb = tCelsius(TWB1)
    # w1 = HAPropsSI('W','P',p1,'B',TWB,'R',rh1) # rasio kelembaban
    mj = 1/V # massa jenis
    _,_,vu = volume_u()
    # print(f'vu= {vu}')
    mu = vu * mj 
    
    # kondisi 2 (yang diinginkan)
    # print(f't2= {t2}')
    if twb<t2:
        # twb lebih kecil dari tdb target
        T2=tKelvin(t2)
        # menghitung RH akhir
    else:
        # suhu bola kering target lebih kecil dari twb. Ini tidak mungkin dilaksanakan
        # karena RH akan lebih besar dari 100%.
        # Untuk mengatasi hal itu, ubah nilai tdb dengan mengambil nilai tengah 
        # dari keduanya. Dengan demikian, nilai RH akan kurang dari 100% dan persamaan
        # dari CoolProp bisa digunakan.
        tdb_rev = twb + kTdb *(t1-twb) # nilai target revisi
        tpesan=(f'Suhu Twb: {round(twb,2)}, shg suhu target ({t2} oC) terlalu rendah, direvisi menjadi {round(tdb_rev,2)} oC')
        T2 = tKelvin(tdb_rev)
    
    # menghitung rh2, w2
    _,_,rh2,_,w2,_ = SI.state("DBT",T2,"WBT",TWB1,p1)
    # rh2 = HAPropsSI('R','P',p1,'B',TWB,'T',T2)
    # w2 = HAPropsSI('W','P',p1,'B',TWB,'T',T2) # rasio kelembaban
    delta_w = w2 - w1 # selisih rasio kelembaban
    delta_ma = mu * delta_w # penambahan massa air
    #print(f'delta_ma= {delta_ma}')
        
    if delta_ma > 0:  
        # bila ada penambahan massa air
        # q_total = debit_sistem_fogging()
        tf_detik=int(delta_ma*1000/(debit_sistem_fogging() * kEvap)) # detik
        # tf_menit=tf_detik/60 # menit
        
        # bulatkan ke kelipatan 5 terdekat
        tf_detik = bulatkan_5terdekat(tf_detik)
        # tf_menit=tf_detik/60 # menit
        
        # cek apakah lebih kecil dari DURASI MINIMAL
        if tf_detik < dMin:
            tf_detik = dMin
                
        # cek apakah lebih besar dari DURASI MAKSIMAL
        if tf_detik > dMax:
            tf_detik = dMax
    else:
        # tidak ada penambahan massa air
        # maka rh tetap
        rh2 = rh1
        delta_ma = 0
        tf_menit = 0
        tf_detik = 0

    return twb, rh2, delta_ma, tf_detik, tpesan

def hitung_fogging_rh(t1,rh1,rh2, kEvap=KOEF_EVAPORASI, dMin=DURASI_FOGGING_MIN, dMax=DURASI_FOGGING_MAX):
    # menghitung lama waktu penyalaan sistem
    # fogging dengan berdasarkan pada 
    # perhitungan kelembaban udara akhir
    # t1, rh1: kondisi awal
    # t2, rh2: kondisi akhir yang diinginkan
    # rh dinyatakan dalam persen
    
    # kondisi awal: t1, rh1
    rh1 = rh1/100 
    p1 = tekanan_u(t1)
    T1 = tKelvin(t1)
    _,_,_,V,w1,TWB = SI.state("DBT",T1,"RH",rh1,p1)
    # TWB = HAPropsSI('B','T',T1,'P',p1,'R',rh1) # suhu bola basah (oK)
    twb = tCelsius(TWB)
    # rasio kelembaban (humidity ratio)
    #w1 = HAPropsSI('W','T',T1,'P',p1,'B',TWB)
    # print(f'w1 = {w1}')
    mj = 1/V #HAPropsSI('V','T',T1,'P',p1,'B',TWB) # massa jenis udara
    _,_,vu = volume_u()
    #print(f'vu= {vu}')
    mu = vu * mj
    #print(f'mu = {mu}')
    
    # Kondisi Akhir: t2, rh2
    rh2 = rh2/100
    if rh2 <1.0:
        # keadaan normal
        TDB,_,_,_,w2,_ = SI.state("RH",rh2,"WBT",TWB,p1)
        # T2 = HAPropsSI('T','P', p1,'B',TWB,'R',rh2) # suhu bola kering
        t2 = tCelsius(TDB)
        # w2 = HAPropsSI('W','P',p1,'B',TWB,'R',rh2) # rasio kelembaban
        #print(f'w2= {w2}')
        delta_ma = w2 - w1
    
        # penambahan massa air
        delta_ma = delta_ma * mu
        #print(f'delta_ma = {delta_ma}')
        if delta_ma > 0:    
            # bila ada penamabahan massa air
            # lama waktu penyalaan sistem fogging
            # q_total = debit_sistem_fogging()
            tf_detik = int(delta_ma*1000/(debit_sistem_fogging() * kEvap)) # detik
            # tf_menit = tf_detik/60           # menit
            
            # bulatkan ke kelipatan 5 terdekat
            tf_detik = bulatkan_5terdekat(tf_detik)
            # tf_menit=tf_detik/60 # menit
        
            # cek apakah lebih kecil dari DURASI MINIMAL
            if tf_detik < dMin:
                tf_detik = dMin
                
            # cek apakah lebih besar dari DURASI MAKSIMAL
            if tf_detik > dMax:
                tf_detik = dMax
        else:
            # tidak ada penambahan massa air
            # suhu dan rh tetap
            t2 = t1
            delta_ma = 0
            #tf_menit = 0
            tf_detik = 0
    else:
        print('Nilai RH >= 1.0. Perhitungan tidak dilaksanakan')
        t2 = t1
        delta_ma = 0
        #tf_menit = 0
        tf_detik = 0
          
    return twb, t2, delta_ma, tf_detik
