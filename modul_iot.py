# -*- coding: utf-8 -*-
"""
Created on Tue Sep 28 18:07:47 2021

@author: muhaemin
"""
import numpy as np
from random import random
import math
import time
from datetime import datetime

def buang_outlier(t0):
    '''
    MEMBUANG DATA OUTLIER DARI SUATU SET DATA

    Parameters
    ----------
    t0 : array numpy

    Returns
    -------
    t1

    '''
    txinfo=di=dt = '-'
    KOEF_OUTLIER = 1.75 # koefisien untuk menentukan batasan atas dan bawah

    t0[t0==0] = np.nan

    t_rata = round(np.nanmean(t0),2)                      # hitung rata-rata
    t_std = round(np.nanstd(t0),2)         #t0.std()                        # hitung standar deviasi
    t_bawah = t_rata - KOEF_OUTLIER *t_std  # batas bawah
    t_atas = t_rata + KOEF_OUTLIER *t_std   # batas atas

    for i in range(t0.size):
        if (t0[i] >= t_atas or t0[i] <= t_bawah):
            di = di + f' {i+1}'; dt = dt + f' {t0[i]}'
            t0[i] = 0.0

    t1=t0
    if not(di==dt): txinfo = f'sensor ke: ( {di[1:]} ) / nilai data: ({dt[1:]})' 
    
    return t1, txinfo

def waktu_str():
    # menentukan waktu sekarang dalam format string
    ct=datetime.now() # waktu sekarang
    cts=ct.strftime('%Y-%m-%d %H:%M:%S')

    return cts

def baca_no_client(str0):
    # membaca nomor client
    # dari string str0 dengan ukuran 3
    # 
    s1=str0[-2:] # ambil 2 karakter terakhir
    a = int(s1)
    return a

def string_ada(fullstring, substring):
    # mengecek apakah suatu substring ada dalam suatu fullstring
    # digunakan untuk mengecek apakah suatu string dari publisher
    # berisi nama client tertentu.
    #
    # fullstring: string utuh yang diterima oleh subscriber 
    # substring : list yang berisi kumpulan nama client
    #
    ada0=[] # mulai dengan list kosong
    N=len(substring)
    for i in range(N-1):
        if fullstring.find(substring[i]) != -1:
            nilai=1  # bila ada 
        else:
            nilai=0  # bila tidak ada
        ada0.append(nilai)
    jml=sum(ada0) # jumlahkan nilai seluruh list
    if jml==0:
        ada=False # bila semuanya 0
    else:
        ada=True
    return ada

def koneksi_info(kode):
    # respon broker ketika ada upaya koneksi
    # dari client
    error={0:'koneksi berhasil',
             1:'koneksi gagal, versi protokol tidak benar',
             2:'koneksi gagal, identifier tidak benar',
             3:'koneksi gagal, server tidak ada',
             4:'koneksi gagal, username/password salah',
             5:'koneksi gagal, tidak mempunyai hak akses'}
    err=error[kode]
    return err

def acak_min_max(min,max):
    # membuat bilangan acak antara min dan max
    a=min+random()*(max-min)
    return a

def acak_normal(rata2,std):
    # membuat sampel bilangan acak dengan distribusi normal
    acak1=random() # bilangan acak dengan distribusi seragam
    acak2=random() # bilaangan acak dengan distribusi seragam
    s=math.sqrt(-2*math.log(acak1))*math.cos(2*math.pi*acak2)
    X=std*s+rata2 # sampel
    return X

def dht_simulasi():
    # simulasi data dari sensor DHT11/DHT22
    # data yang keluar dianggap normal dengan nilai rata-rata
    # dan standar deviasi seperti dibawah ini
    
    suhu_min=15;suhu_max=50
    suhu_rata2=27.1510; suhu_std=4.2467
    rh_min=40; rh_max=100
    rh_rata2=80.918; rh_std=15.634
    
    # hitung suhu
    suhu=acak_normal(suhu_rata2,suhu_std)
    if suhu<suhu_min:
        suhu=suhu_min
    if suhu>suhu_max:
        suhu=suhu_max
    suhu=round(suhu,2) # 2 angka di belakang koma
    
    # hitung suhu
    rh=round(acak_normal(rh_rata2,rh_std),1)
    if rh<rh_min:
        rh=rh_min
    if rh>rh_max:
        rh=rh_max
    rh=round(rh,1) # 1 angka di belakang koma
    return rh,suhu

def berisi_titik_koma(str0):
    # mengecek apakah suatu string
    # berisi titik atau koma
    # --> string bisa diubah ke bilangan
    titik='.'
    koma=','
    a=titik in str0
    b=koma in str0
    c=False
    if a or b == True:
        c=True
    return c

def berisi_kolon_strip(str0):
    # mengecek apakah suatu string berisi titik (colon) dua
    # dan atau strip.
    # Bila benar, ini adalah string waktu
    kolon=':'
    strip='-'
    a=kolon in str0
    b=strip in str0
    c=False
    if a or b == True:
        c=True
    return c

def parsing3(str0):
    # memotong string menjadi komponennya 
    # berdasarkan delimiter yang digunakan
        
    delimiter=';'
    jml_kata=str0.count(delimiter)+1
    st=[] # list utk komponen string
    i=0 # nomor huruf
    j=0 # nomor komponen
    s=''
    while i<len(str0):
        c=str0[i]
        if c!=delimiter:
            s=s+c    
        else:
            st.append(s)
            s=''
            j=j+1
        i=i+1
    st.append(s) # komponen str0 dengan tipe string
    return st

def parsing4(str0):
    # memotong string str0 menjadi komponennya 
    # berdasarkan delimiter yang digunakan
    # dan mengubahnya menjadi angka atau tetap berupa string
    #
    delimiter=';'
    jml_kata=str0.count(delimiter)+1
    st=[] # list utk komponen string
    i=0 # nomor huruf
    j=0 # nomor komponen
    s=''
    while i<len(str0):
        c=str0[i]
        if c!=delimiter:
            s=s+c    
        else:
            st.append(s)
            s=''
            j=j+1
        i=i+1
    st.append(s) # komponen str0 dengan tipe string
    
    jml_komponen=len(st)
    k=[] # list yang berisi komponen strin yang sudah dikonversi ke numerik
    for i in range(jml_komponen):
        if st[i].isalnum()==True:
            # mengandung karakter huruf
            k.append(st[i])
        elif st[i].isnumeric()==True:
            # seluruh komponen berupa angka
            k.append(int(st[i]))
        elif berisi_titik_koma(st[i])==True:
            # berisi titik dan atau koma
            k.append(float(st[i]))
        else: 
            # data dengan format waktu
            k.append(st[i])  
    return k

def waktu_bulatdetik(tawal,takhir):
    sinta  = (tawal-takhir).total_hours()
    sintb  = (tawal-takhir).total_minutes()
    sintc  = (tawal-takhir).total_seconds()
    sint  = datetime(tawal.year, tawal.month, tawal.day, sinta, sintb, sintc, 0)
    sint  = sint.strftime('%H:%M:%S')
    return sint
