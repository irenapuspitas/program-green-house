# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 10:35:30 2023

@author: LENOVO
"""

#import module
import paho.mqtt.client as mqtt
import threading
import os
import time
#import math
import numpy as np
import modul_iot as mi
import modul_osfile_tux as osft
import modul_evapcool_psy_rev1 as eva3
from datetime import datetime, timedelta
import modul_status_client as msc
import socket
#import curses
#from curses.textpad import Textbox, rectangle

ver='9n.01b'
#os.system('clear')
#os.system('python3 --version')
print(f'Versi Program #{ver}\n--------------------')

global prosesON, logprint, str_onMsg, top_onMsg
prosesON  =False                 #mulai PROSES, jika waktu tunggu awal sudah 
lockscreen=0                     #nilai 1, akan lock screen saat mulai running, 0 akan dibypass
logprint  = []                   #simpanan informasi Log utk dicetak diakhir baris
str_onMsg = top_onMsg = ""       #nilai awal pesan di on_message

def cek_koneksi():
    global status_koneksi 
    
    hostname = "192.168.1.211"
    response = os.system ("ping -c 1 " + hostname)

    #check the response

    if response == 0:
        status_koneksi = True
        print(hostname, 'Berhasil terhubung ke jaringan')
        
    else: 
        status_koneksi = False 
        print(hostname, 'Gagal terhubung ke jaringan')
       

status_koneksi = False
while True:
    if status_koneksi == False:
        cek_koneksi()
        time.sleep(6)
    else : 
        break

def jeda_antar_fogging(suhu):
    # mengatur waktu jeda minimal antar fogging
    # jeda
    #   suhu rendah -> 120 detik
    #   suhu sedang -> 60 detik
    #   suhu tinggi -> 30 detik
    BATAS_SUHU_RENDAH = 25
    BATAS_SUHU_SEDANG = 27

    if suhu <= BATAS_SUHU_RENDAH:               jf = 120
    else:
        if suhu <= BATAS_SUHU_SEDANG:           jf = 60
        else:                                   jf = 36     # suhu tinggi
    return int(jf)

def on_connect(client, userdata, flags, rc):
    if rc ==0:           ps=f">> TERSAMBUNG DENGAN BROKER, dengan kode: {rc}"
    else:                ps=f">> GAGAL tersambung ke BROKER, kode error: {rc}"
    logprint.append(f"{ps}")
    
    #while True:
    #    try:
    #       client.connect(broker,1883,60)
    #       client.on_connect = on_connect
    #       client.loop_forever()
    #   except (ConnectionError,socket.timeout, socket.error):
    #       print("Gagal terhubung ke broker, mencoba terhubung kembali")
    #       time.sleep(5)
            
def on_message(client, userdata, msg):
    # fungsi callback yang akan bekerja bila client menerima pesan dari broker
    
    #global NAMA_CLIENT, client_TRH, suhu, rh, koreksiJEDA_AWAL, msg_prev, izinAct, stAct_gpio, datclient_NOL, cekclient_ERR
    global str_onMsg, top_onMsg
    #limitNOL_rusak=10                            # limit nilai data NOL berturut-turut, client dinyatakan rusak

    str0=str(msg.payload.decode("utf-8"))
    str_onMsg = str0
    top_onMsg = msg.topic
    
def proses_onMessage():
    # fungsi callback yang akan bekerja bila client menerima pesan dari broker
    
    global str_onMsg, top_onMsg, NAMA_CLIENT, client_TRH, suhu, rh, koreksiJEDA_AWAL, msg_prev, izinAct, stAct_gpio, datclient_NOL, cekclient_ERR, suhuOut, rhOut
    limitNOL_rusak=10                            # limit nilai data NOL berturut-turut, client dinyatakan rusak
    waktu_sekarang=mi.waktu_str()
    waktu = mi.waktu_str()
    waktu_jam = waktu[11:]
    data_log = f'{waktu_jam};{prosesON};{str_onMsg}'

    if (str_onMsg != msg_prev):
        # pesan folder / nama file + header
        namafile = osft.prepDir("Log_subs","Waktu;prosesON;ClientID;data1;data2;data3;data4;no_urut\n")
        if (str_onMsg.find('Off')<0):    osft.save_csv(namafile, data_log)       # hanya simpan yg tidak Off
        logprint.append(f'[] SUB: {top_onMsg} - {data_log}')
        msg_prev=str_onMsg

        # cek apakah string berisi nama client
        if mi.string_ada(str_onMsg,NAMA_CLIENT)== True:
            k=mi.parsing4(str_onMsg)
            ns=int(mi.baca_no_client(k[0])) # nomor stasiun

            #client_TRH=[1,2,3]
            client_TRH=msc.R_nomor_clientTRH()
            if ns in client_TRH: 
                # UPDATE status client
                msc.update_status_CLI(str_onMsg)
                
                ks1=KSI[0];ks2=KSI[1]
                kr1=KRI[0];kr2=KRI[1]
                kldr=KLDR[0]
                
                pg=ARR_DIC[ns]
                #pg1=ARR_DICT[ns]
                pg2=ARR_DIC2[ns]
                
                s1=pg[0];s2=pg[1]
                s5=pg2[0]

                suhu[s1]=k[ks1]
                suhu[s2]=k[ks2]
                
                rh[s1]=k[kr1]
                rh[s2]=k[kr2]
         
                #suhuOut[s1]=k[ks1]
                #suhuOut[s2]=k[ks2]
                #rhOut[s1]=k[kr1]
                #rhOut[s2]=k[kr2]
                
                ldr[s5]=k[kldr]

                sub_dt[ns-1]=datetime.now()

            if top_onMsg == 'iklim/out/01':   
                suhuOut=k[1]; rhOut=round(k[2],1)
                pr_info.append(f"Suhu/RH lingkungan : {suhuOut} / {rhOut}")
                os.system(f"echo 'top: {waktu_jam} Suhu/RH lingkungan : {suhuOut} / {rhOut}' >> /home/pi/txt/__cek_OUT.txt")
     
            if ns == 31:   
                suhuOut=k[1]; rhOut=round(k[2],1)
                pr_info.append(f"Suhu/RH lingkungan : {suhuOut} / {rhOut}")
                os.system(f"echo 'ns31: {waktu_jam} Suhu/RH lingkungan : {suhuOut} / {rhOut}' >> /home/pi/txt/__cek_OUT.txt")

            client_KIFO=[5,6]
            if ns in client_KIFO:
                cl_kode=k[1];                     cl_data=k[2]
                if cl_kode.find('gpio')>=0:       
                    stgpio = f'-> status GPIO, {stAct_gpio}'
                    stgpio = stgpio.replace("{",'');                    stgpio = stgpio.replace("}",'')
                    stgpio = stgpio.replace("6:",'Fogging:');           stgpio = stgpio.replace("5:",'Kipas:')
                    stgpio = stgpio.replace("'",'');
                    pr_info.append(stgpio)

                    # os.system(f"echo '{waktu_jam} {stgpio}' >> /home/pi/txt/cek_gpio.txt")
                if cl_kode.find('ON')>=0:         izinAct[ns-4]=1; stAct_gpio[ns][2]=cl_data
                if cl_kode.find('OFF')>=0:        izinAct[ns-4]=0; stAct_gpio[ns][3]=cl_data;
                
                if cl_kode.find('fogging_NOW')>=0:
                    if cl_data!='00000':         izinAct[ns-4]=0; stAct_gpio[ns][2]=cl_data
                    else:                         izinAct[ns-4]=1; stAct_gpio[ns][3]=cl_data
                if   cl_kode.find('kipas_NOW')>=0: 
                    if cl_data!='00000':        izinAct[ns-4]=0; stAct_gpio[ns][2]=cl_data
                    else:                         izinAct[ns-4]=1; stAct_gpio[ns][3]=cl_data
                    
                # cek waktu sisa ON
                if (cl_kode=='koreksi_waktu'): 
                    if koreksiJEDA_AWAL<int(cl_data): koreksiJEDA_AWAL=int(cl_data)
                    
                #reset    
                cl_data='-'

def subscribe_dhti(broker, topik, jeda):  
    #subscriber untuk data dari sensor di dalam GH
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_log=on_log
    client.on_message = on_message
    
    # tentukan pesan yang dikirimkan bila client mati secara abnormal
    client.will_set(topik, b'{"status": "Off"}')
    
    # buat koneksi ke broker
    client.connect(broker, 1883, 60)
    client.subscribe(topik)
    while True:
        try:
           #buat loop koneksi ke broker           
           client.loop_start()
           time.sleep(3) # dibuat jeda untuk memberi waktu bagi client utk menerima dan proses pesan
           client.loop_stop()  
        except Exception as e:
           print("Error connecting to broker")
           time.sleep(5)
           try: 
               client.reconnect()
               client.loop_start()
           except Exception as e:
               print("Error reconnecting to broker")
                
def on_log(client, userdata, level, buf):
    # menampilkan data log dari koneksi yang dilakukan
    # print("log: ",buf)
    log=''

def publikasi_pesan(broker, client, ftopik, fpesan):
    # tentukan pesan yang dikirimkan bila client mati secara abnormal
    client.will_set(ftopik, b'{"status": "Off"}')
    try:
       client.connect(broker, 1883, 60)
    except Exception as e:
           print("Koneksi ke broker terputus, mencoba terhubung kembali..")
           time.sleep(5)
           try: 
              client.reconnect()
           except Exception as e:
              print("Error reconnecting to broker")
                
    waktu = mi.waktu_str()
    waktu_jam = waktu[11:]

    client.publish(ftopik, payload=fpesan, qos=0, retain=False)
    log_pubs = f"{waktu_jam};{prosesON};{ftopik};{fpesan}"
    
    # pesan folder / nama file + header
    namafile = osft.prepDir("Log_pubs","Waktu;prosesON;Topik;Pesan\n")
    osft.save_csv(namafile, log_pubs)
    logprint.append(f"[] PUB: {log_pubs}")
    
#def read_data_from_local():
#    n = Data_hasil
#    file_name = {n} 
#    file_path = 
    
#    with open(file_path,newline='') as csvfile:
#        reader = csv.reader(csvfile)
    
#        next(reader)
        
#        for columns in reader:
#            suhu = columns[7]
#            rh = columns [9]
         
#lock windows gui
#if lockscreen==1: #mate-screensaver-command -l     #ctypes.windll.user32.LockWorkStation() 

# ************************************************************
# ****************** PROGRAM UTAMA ***************************

# data/inisiasi client
NAMA_CLIENT = ['c00','c01','c02','c03','c04','c05','c06','c07','c08','c09','c10']
NAMA_CLIENT = NAMA_CLIENT + ['c11','c12','c13','c14','c15','c16','c17','c18','c19','c20','c31']    

# topik publikasi
topik_kipas="kipas/act"
topik_fogging="fogging/act"
topik_disp02="display02"
topik_dtime="update/dtime"
topik_maintain="maintain/update"

kode_client="c00"   #client pengirim, c00 -- sbg utama
client_TRH=msc.R_nomor_clientTRH()

# set topik THREAD
topik1='iklim/gh/01'
topik2='iklim/gh/02'
topik3='iklim/gh/03'
topik4='iklim/gh/04'
topik5='aktuator/infokipas'
topik6='aktuator/infofogging'
#topik6='iklim/out/02'

BROKER_EMQX="broker.emqx.io"
BROKER_MSK="192.168.43.17"
BROKER_UNPAD="10.76.51.202"

BROKER_HIDROPONIK0="192.168.1.211"
BROKER_HIDROPONIK1="192.168.1.212"
broker=BROKER_HIDROPONIK0

# cek switch broker
# switch_broker=int(cek_switch_broker())
# if switch_broker==1: broker=BROKER_HIDROPONIK1

# parameter utama iklim max 6 titik (sensor DHT: suhu dan rh
suhu = np.zeros(8);              rh = np.zeros(8)
suhu_out = np.zeros(4);          rh_out = np.zeros(4)
ldr = np.zeros(4)
suhu_in= np.zeros(4);            rh_in=np.zeros(4)
# moving average suhu, dengan lebar banyak data lw/jw
lw = 5;                          suhu0 = np.zeros(lw);
jw = 5;                          rh0 = np.zeros(lw);

# jeda pengukuran dan looping
JEDA_PENGUKURAN=9.98
JEDA_AWAL=60               # detik, waktu tunggu awal program start, memberi kesempatan pengukuran stabil
JEDA_ANTAR_PUB=36         # detik, jeda antar perintah eksekusi kipas/fogging
JEDA_LOOPTHREAD=10

# kamus penempatan posisi data suhu dan rh dari 3 client
# ke dalam variabel global
KSI=[1,3] # indeks data suhu dalam data list dari client
KRI=[2,4] # indeks data rh dalam data list dari client
KLDR=[5]
ARR_DIC={1:[0,1],2:[2,3],3:[4,5],4:[6,7]} # posisi suhu dan rh untuk tiap client
#ARR_DICT={3:[0,1],4:[2,3]}
ARR_DIC2={1:[0],2:[1],3:[2],4:[3]} # posisi ldr untuk tiap client 

# setting THREAD STARTER
s1=threading.Thread(target=subscribe_dhti,args=(broker,topik1,JEDA_LOOPTHREAD),daemon=True)
s2=threading.Thread(target=subscribe_dhti,args=(broker,topik2,JEDA_LOOPTHREAD),daemon=True)
s3=threading.Thread(target=subscribe_dhti,args=(broker,topik3,JEDA_LOOPTHREAD),daemon=True)
s4=threading.Thread(target=subscribe_dhti,args=(broker,topik4,JEDA_LOOPTHREAD),daemon=True)
#s5=threading.Thread(target=subscribe_dhti,args=(broker,topik5,JEDA_LOOPTHREAD),daemon=True)
#s6=threading.Thread(target=subscribe_dhti,args=(broker,topik6,JEDA_LOOPTHREAD),daemon=True)

s1.start();        s2.start();        s3.start();      s4.start();
#s5.start();        s6.start();

# ukuran utama GH # >> SUDAH ADA DI MODUL evapcool

# definisi client mqtt
client = mqtt.Client()

# suhu dan rh target dan trigger
SUHU_MAX = 30.00;                          RH_MIN = 60.00  # berdasarkan sifat tanaman
SUHU_DELTA= 6.00;                          RH_DELTA = 15.00 # dipilih untuk menentukan kapan aktivasi aktuator dilaksanakan

# nilai suhu dan rh yang akan mengaktifkan aktuator
suhu_trigger= SUHU_MAX - SUHU_DELTA;       rh_trigger = RH_MIN + RH_DELTA

# nilai suhu dan rh target
suhu_target = SUHU_MAX - 4;                rh_target = RH_MIN + 20
rh_koreksi = 0

# modifikasi suhu input untuk perhitungan waktu fogging
t0 = suhu_trigger + 4

# inisiasi kipas dan sistem fogging
data_kipas='00000';                             data_fogging='00000'
durasi_kipas=0;                                 durasi_fogging=0
kipasON=False;                                  foggingON=False
izinActs='OPEN'                                # string: OPEN (aktuator bisa menerima perintah) atau Close
izinAct=np.zeros(3)                            # index 0/1/2 = utama, kipas, fogging
stAct_gpio={6:['','','',''],5:['','','','']}   # status: no counter utama - data - gpio ON client - gpio OFF client
responFOG=responKIP='-  '
msg_prev='-'


# inisiasi waktu/tgl/hari/waktu hitung
ti_awal = ti_prev = waktu_berikutnyaTM = sekarang = datetime.now();
ti_sejak = mi.waktu_str()

sub_dt = [ti_awal,ti_awal,ti_awal,ti_awal];         sub_dts = np.zeros(4)
tFOG_berakhir = tFOG_mulai = tKIP_mulai = ti_awal
str_tupd=jH=''
statsubRST=[0,0,0,0]
u_dtma = u_durt = u_dura = srh = stwb = '-'            # inisiasi nilai perhitungan
ts_actf=0.0                                 # sisa waktu JALANnya aktuator
tsisa_act=txtsisa=txtsisb='-'

# set var list/array untuk gradien suhu; dan nilai awal tRata dan tMov
t_gradien=0.0;                              n_grad =np.zeros(5)
t_prev=0.0;                                 rh_prev=0.0
tRata=0;                                    tMov=0
rhRata=0;                                   rhMov=0

ti_Awal_MulaiProses = ti_awal + timedelta(seconds=JEDA_AWAL)  # waktu tunggu mulai aksi
act_durasi=used_durasi =0
tot_ma=used_deltama=0.0                # nilai awal durasi/massa air yang jadi digunakan
koreksiJEDA_AWAL=0
jeda_perintahKIP = 60           # detik, selisih waktu jalannya kipas dari fogging

# limit, variabel nilai batas
sLimit,sorder = osft.setLIMIT()             # limit waktu RESTART program
limit_sub=400                               # limit bila SUB/data tidak masuk, melebihi limit -> program akan RESTART

pr_info= []                                  # preserve, inisiasi variabel cetak/print, info
dLoop  = True                                # loop program utama, bisa diset False untuk berhenti, bila diperlukan

c = 0                                       # counter
nf = __file__

# PROSES AWAL
txfile=f"/home/pi/Documents/program_model_gh/txt/{ti_awal.strftime('%Y%m')}_log_boot.txt"
#os.system(f'echo {ti_awal} / START ON: {nf[19:]} >> {txfile}')

# simpan sesi waktu proses UTAMA, per {tm} menit
fnsesi_utama = "/home/pi/Documents/program_model_gh/txt/dtsesi_utama.txt"
dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')                  
#os.system(f"echo '{dt}' > {fnsesi_utama}")

tKondusif = False

while dLoop:
    c=c+1
    ### PROSES NORMAL
    # catat waktu sekarang
    ti_now = datetime.now()
    tTotal = ti_now-ti_awal;    tTotal = int(tTotal.total_seconds())
    ttj   = tTotal//3600;   ttm   = int((tTotal%3600)//60);     tts   = int((tTotal%3600)%60)
    tTotal = datetime(ti_now.year, ti_now.month, ti_now.day, ttj, ttm, tts, 0)
    tTotal = tTotal.strftime('%H:%M:%S')
    
    #os.system(f'echo {tTotal} >> /home/pi/txt/__cek.aja.txt')
    
    #### proses data yang masuk dari on_message
    proses_onMessage()

    # pengecekan setiap 5 menit
    tm = 5
    if sekarang >= waktu_berikutnyaTM:
        waktu_berikutnyaTM = sekarang + timedelta(minutes=tm)

        # simpan sesi waktu proses UTAMA, per {tm} menit
        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')           
        os.system(f"echo '{dt}' > {fnsesi_utama}")
    
    tSiklus= round(float(ti_now.timestamp()-ti_prev.timestamp()),2)

    if c==1:        # seting awal
        tSiklus=0.00;   tTotal = ti_now-ti_now      # di nol kan
        
        print('\nPersiapan...\n')
        time.sleep(2)                 # memberi waktu membaca data awal
        for i in range(len(logprint)):
            if logprint[i].find('BROKER')>0: print(logprint[i])
        logprint=[]   # dikosongkan lagi
        time.sleep(1)                 # memberi waktu membaca data awal
       # os.system('clear')

        # kirim pesan untuk UPDATE waktu client
        tupd = datetime.now() + timedelta(seconds=2)
        str_tupd = tupd.strftime('%Y-%m-%d %H:%M:%S')
        
        payload_str=kode_client+";update_time;"+str_tupd+";"+str(c)
        topik_pub = [topik_fogging, topik_kipas, topik_dtime, topik_disp02, topik_maintain]
        for t in range(len(topik_pub)):
            publikasi_pesan(broker,client, topik_pub[t], payload_str)

        # cek kondisi AKTUATOR (kipas)
        data_fogging='00000';       data_kipas='00000';       durasi_cek=40
        payload_str1=kode_client+";"+data_kipas+";"+str(int(durasi_cek))+";"+str(c)
        publikasi_pesan(broker,client, topik_kipas, payload_str)
        payload_str2=kode_client+";"+data_fogging+";"+str(int(durasi_cek))+";"+str(c)
        publikasi_pesan(broker,client, topik_fogging, payload_str)
        
### ---
    ### mulai

    ti_prev=ti_now      # reset ti_prev\

    #print header keterangan
    print("===============================================================")
    print(f"sesi ke        :{c}") 
    #print(f"Waktu Sekarang : {}")
    print(f"Waktu Siklus   :{tSiklus}")
    print(f"Total          :{tTotal}")  
    print(f"Versi          :{ver}")     
    print(f"File           :{nf[19:]}")
    print(f"Sejak          :{ti_sejak}")
    
    # info kondisi iklim kondusif ?
    txtpesan='-'
    if tKondusif == True:
        txtpesan="-> kondisi KONDUSIF"
        print("-> kondisi KONDUSIF")
        if (used_durasi==0 and izinActs=='OPEN'):
            txtpesan = txtpesan + ", tidak dilakukan pendinginan"
            print("{txtpesan}, tidak dilakukan pendinginan")
        if txtpesan!='-':  pr_info.append(txtpesan) 

    #print nilai input suhu dan RH
    print("===============================================================")
    print("[ DATA ]")
    print(f"Sensor, SUHU (oC) : {suhu}")
    print(f"RH (%)            : {rh}")
    print(f"Suhu luar         : {suhu_out}")
    print(f"RH luar           : {rh_out}")
    print(f"LDR               : {ldr}")
    
    # bersihkan outlier
    #if c>1:
    #    txtinfo='-'
    #    suhu,txtinfo = mi.buang_outlier(suhu);
    #    if txtinfo!='-': pr_info.append(f"-> outlier suhu, {txtinfo}")
    #    rh,  txtinfo = mi.buang_outlier(rh);
    #    if txtinfo!='-': pr_info.append(f"-> outlier rh,   {txtinfo}")
    txt_headL = "PERHITUNGAN"
    # header 1+area 2, dimunculkan dulu
  
    # hitung rata-rata suhu dan rh
    # bila rata-rata suhu dan rh sudah tidak sama dengan 0, 
    # hitung rata-rata suhu dan rh dengan mengabaikan nilai 0

    bla=4
    ### PROSES NESTED #1: proses dilakukan bila rata2 suhu tidak NOL
    _ = np.mean(suhu)
    if _ !=0:
        # hitung suhu dan rh rata-rata: tRata, rhRata
       
        
        suhu_in=[suhu[0],suhu[1],suhu[2],suhu[3]]
        rh_in=[rh[0],rh[1],rh[2],rh[3]]
        suhu_out=[suhu[4],suhu[5],suhu[6],suhu[7]]
        rh_out=[rh[4],rh[5],rh[6],rh[7]]
        
        suhu[suhu==0] = np.nan;                       rh[rh==0] = np.nan # ubah 0 --> NaN
        tRata=round(np.nanmean(suhu_in),2);           rhRata=round(np.nanmean(rh_in))
                 
        # update proses moving average dengan list dari numpy
        suhu0[0]=tRata;                               rh0[0]=rhRata
        suhu0[suhu0==0] = np.nan;                     rh0[rh0==0] = np.nan # ubah 0 --> NaN
        tMov = round(np.nanmean(suhu0),2);            rhMov = round(np.nanmean(rh0));
        
        suhu_outRata= (float((suhu[4]+suhu[5]+suhu[6]+suhu[7])/4))            
        rh_outRata= (float((rh[4]+rh[5]+rh[6]+rh[7])/4))
        #pengecekan nilai suhu dalam    
        #if suhu_in[suhu_in== np.nan ]:
              
        print(f"5 rata - rata suhu terakhir : {suhu0}")
        print(f"5 rata - rata RH terakhir   : {rh0}")
        print(f"Suhu luar Rata - rata       : {suhu_outRata}")
        print(f"RH luar Rata - rata         : {rh_outRata}")
        # tampilkan 5 data terakhir data suhu, RH -> untuk Moving Average
        # setelah proses selesai, roll, shift/geser index list
        suhu0=np.roll(suhu0,1);                       rh0=np.roll(rh0,1)

        blb=bla+5
        print(f"rata-rata suhu : {tRata}")
        print(f"rata-rata rh   : {rhRata}")
        print(f"mov avg suhu   : {tMov}")  
        print(f"mov avg rh     : {rhMov}")
        # antisipasi jika pembagi tsiklus (jika NOL error), untuk perhitungan gradien suhu
        if tSiklus>0:
            # t_prev: suhu sebelumnya; t_gradien: nilai graden suhu/siklus; n_grad: naik/tetap/turunnya (1,0,-1) gradien
            if t_prev>0: t_gradien=round((tMov-t_prev)/(tSiklus/60),3)             # dibuat permenit
            
            if(t_gradien>0):            n_grad[0]=1
            elif(t_gradien)==0:         n_grad[0]=0
            else:                       n_grad[0]=-1

            sum_5grad = int(np.sum(n_grad))             # sumasi 5 grad terakhir
            waktu = mi.waktu_str()
            namafile = osft.prepDir("Data_gardien","Waktu;sesi_ke;prosesON;n_grad_ow;t_gradien;tMov_now;t_prev;sum2grad;tSiklus\n")
            data_grad=f"{waktu};{c};{prosesON};{int(n_grad[0])};{t_gradien};{tMov};{t_prev};{sum_5grad};{tSiklus}"
            osft.save_csv(namafile, data_grad)

            txgrad=''
            if t_gradien>=0: txgrad=f' {t_gradien}'
            else:            txgrad=f'{t_gradien}'
            print(f"Gradien:{txgrad} oC/menit")
            print(f"Suhu sebelumnya {t_prev} --> Suhu selanjutnya, {tMov}")
            print(f"Lima gradien : {sum_5grad}")
            print(f"Nilai gradien: {n_grad[1]}")
            
            t_prev=tMov                            # tMov saat ini, disimpan sbg t_prev, untuk perhitungan berikutnya
            rh_prev=rhMov
            n_grad=np.roll(n_grad,1)               # geser/shift index list
            
        # waktu tunggu JEDA AWAL
        if(koreksiJEDA_AWAL>0 and prosesON==False):
             ti_Awal_MulaiProses = ti_awal + timedelta(seconds=koreksiJEDA_AWAL+JEDA_ANTAR_PUB)  # waktu tunggu mulai aksi
             if (koreksiJEDA_AWAL+JEDA_ANTAR_PUB)>60: 
                pr_info.append(f"-> program ini di-MULAI, sementara aktuator masih BERJALAN!") 
                print(f"-> program ini di-MULAI, sementara aktuator masih BERJALAN!")
        else:
             ti_Awal_MulaiProses = ti_awal + timedelta(seconds=JEDA_AWAL) # waktu tunggu mulai aksi
             
        # tampilkan data SET, apakah suhu dan rh trigger sudah dilampaui
        # inisiasi variabel perhitungan coolprop
        t1 =tMov;                            rh1 =rhMov
        t2 =suhu_target;                     rh2 =rh_target 
       
        print("===============================================================")
        print("[ INPUT ]")
        print(f"Awal Suhu    : {round(t1,2)}")           
        print(f"Awal RH      : {round(rh1,2)}")
        print(f"Target Suhu  : {round(t2,2)}") 
        print(f"Target RH    : {round(rh2,2)}")
        print(f"Trigger Suhu : {round(suhu_trigger,2)}")
        print(f"Trigger rh   : {round(rh_trigger,2)}")

        ### PROSES NESTED #2: proses perhitungan setelah waktu tunggu awal (1 menit) terlampaui
        if (ti_now<=ti_Awal_MulaiProses):
            ttg = (ti_Awal_MulaiProses-ti_now).total_seconds()
            ttg = datetime(ti_now.year, ti_now.month, ti_now.day, 0, int(ttg//60), int(ttg%60), 0)
            ttg = ttg.strftime('%H:%M:%S')
            #ttg = mi.waktu_bulatdetik(ti_now,ti_Awal_MulaiProses) -- masih ERROR
            
            pr_info.append(f"-> proses AKAN mulai dalam ({ttg}) detik")
            print(f"-> proses AKAN mulai dalam {ttg} detik")
        else:
            prosesON = True
 
            # set nilai jeda antar perintah fogging/kipas
            JEDA_ANTAR_PUB = int(jeda_antar_fogging(tMov))

             # pengecekan kondisi lingkungan iklim GH, apakah Kondusif
            txtpesan='-'
            if (tMov >= suhu_trigger and rhMov <= rh_trigger):  tKondusif = False
            else: tKondusif = True
                
            # cek GRADIEN untuk kondisi Kondusif dan koreksi RH
            if ((tMov-suhu_target)<=2.3 and sum_5grad<=-4):
                # KONDUSIF berdasarkan turunnya gradien
                if tKondusif==False: 
                   pr_info.append(f"-> GRADIEN turun, selisih suhu: {round((tMov-suhu_target),2)}, sum grad: {sum_5grad} [kondusif ?]")
                   print(f"-> GRADIEN turun, selisih suhu: {round((tMov-suhu_target),2)}", "sum grad: {sum_5grad}","[kondusif?]")
                # rh dikoreksi
                rh_koreksi=-2.7
                tKondusif = True
            elif ((tMov-suhu_target)<=3.5) and (sum_5grad<=(-3)): 
                # berdasarkan turunnya gradien, rh dikoreksi
                pr_info.append(f"-> sum grad: {sum_5grad} / selisih suhu: {round((tMov-suhu_target),2)}")
                print(f"-> sum grad: {sum_5grad} / selisih suhu: {round((tMov-suhu_target),2)}")
                if rh_koreksi ==0: rh_koreksi=-1.25
            else:
                rh_koreksi=0
            
            # koreksi rh bila ada
            rh_trigger = RH_MIN + RH_DELTA + rh_koreksi

            if tKondusif == True and foggingON==False and kipasON==False:
                txt_headL = 'PERHITUNGAN'
                u_dtma = u_durt = u_dura = srh = stwb = '-'
                
            ### PROSES NESTED #3: proses UTAMA, analisis dan perhitungan kondisi iklim GH
            elif (tKondusif==False and used_durasi==0 and izinActs=='OPEN'):
                 # lakukan perhitungan
                 tnow=datetime.now()

                 # penentuan waktu nyala kipas
                 debit =eva3.KIPAS_DEBIT * eva3.KIPAS_JML
                 wk = eva3.kipas_lama_nyala()
                 kipas_waktu_nyala= wk               # saat ini waktu kipas mengikuti waktu fogging
                 
                 # perhitungan berdasarkan RH
                 # print('PERHITUNGAN BERDASARKAN RH')
                 # twb, t2, d_ma, tf_byRH = eva3.hitung_fogging_rh(tRata,rhRata, rh_target,GH_ELEV,vu_total)
                 
                 # input suhu = rata-rata suhu sekarang dan suhu input sebelumnya
                 t1 = (t0 + tMov)/2
                 t1 = np.maximum(t1,tMov)            # t1 yang diambil yang terbesar antara t1 dan tmov

                 twb, t_hasil, delta_rhma, tf_rhdetik = eva3.hitung_fogging_rh(t1,rh1,rh2)
                 # print('     twb                  : ', round(twb,1), ' oC')
                 # print('     t hasil              : ', round(t_hasil,1), ' oC')
                 # print('     Penambahan massa air : ', round(delta_ma,2))
                 # print('     Lama waktu fogging   : ', round(tf_rhdetik,2), ' menit')
                 
                 # perhitungan berdasarkan suhu (t2)
                 txtpesan='-'
                 twb, rh2, delta_shma, tf_shdetik, txtpesan = eva3.hitung_fogging_suhu(t1,rh1,t2)
                 if txtpesan != '-':
                    pr_info.append(f'-> {txtpesan}')
                    print(f"-> {txtpesan}")

                 # set durasi fogging berdasar durasi terlama (hitungan RH atau Suhu)
                 delta_ma = np.maximum(delta_rhma,delta_shma)
                 durasi_fogging = int(np.maximum(tf_rhdetik,tf_shdetik))
                 # pencatatan durasi yang digunakan, dan massa air yang diberikan (untuk di SAVE)
                 used_deltama  = delta_ma;            used_durasi = durasi_fogging
                 tFOG_mulai    = tnow;                tKIP_mulai  = tnow + timedelta(seconds=jeda_perintahKIP)
                 tot_ma = round(tot_ma+used_deltama,2)

                 # perhitungan berdasarkan suhu (t2)
                 txt_headL = 'PERHITUNGAN (BERDASARKAN SUHU BOLA KERING)'
                 srh  = str(round(rh2*100,2)) + ' %'
                 stwb = str(round(twb,1)) + ' oC'
                 # tampilan hasil analisis
                 u_dtma = f'{round(used_deltama,2)} kg'
                 u_durt = f'{round(used_durasi,2)} dtk ({round(used_durasi/60,2)} mnt)'
            else:
                 txt_headL = 'HASIL PERHITUNGAN YANG DITERAPKAN'
                 srh = stwb = '-'
                 # tampilan hasil analisis
                 u_dtma = f'{round(used_deltama,2)} kg'
                 u_durt = f'{round(used_durasi,2)} dtk ({round(used_durasi/60,2)} mnt)'
            
            # ***** SET PERINTAH FOGGING *****
            if (foggingON==False and izinActs=='OPEN' and used_durasi>0):
                #setup untuk publikasi pesan
                data_fogging = '11111'    # nilai data
                
                payload_str=kode_client+";"+data_fogging+";"+str(int(durasi_fogging))+";#"+str(c)
                publikasi_pesan(broker,client, topik_fogging, payload_str)
                foggingON=True
                
                tFOG_berakhir = tnow + timedelta(seconds=durasi_fogging)
                t0 = t1         # disimpan untuk koreksi berikutnya
                
                # simpan status ACT
                stAct_gpio[6]=[str(c),data_fogging,'','']
                logprint.append(f'[] GPIO: {stAct_gpio}')
            
            tnow=datetime.now()
            # ***** SET PERINTAH KIPAS *****
            # kipas dinyalakan jika/selama fogging ON, dan durasi kipas > 0
            
            if (kipasON==False and izinActs=='OPEN' and used_durasi>0 and tnow>=tKIP_mulai):
                # cek durasi kipas
                if durasi_fogging>jeda_perintahKIP: durasi_kipas=durasi_fogging-jeda_perintahKIP
                else: durasi_kipas=40  #durasi minimum
                
                #setup untuk publikasi pesan
                data_kipas = '11111'      # nilai data
                        
                payload_str=kode_client+";"+data_kipas+";"+str(int(durasi_kipas))+";#"+str(c)
                publikasi_pesan(broker,client, topik_kipas, payload_str)
                kipasON=True
                tKIP_berakhir = tnow + timedelta(seconds=durasi_kipas)

                # simpan status ACT
                stAct_gpio[5]=[str(c),data_kipas,'','']
                logprint.append(f'[] GPIO: {stAct_gpio}')
                
            ### END nested #3 akhir perhitungan

            # --> penyelesaian hitung sisa waktu
            ### proses ini di dalam nested #3, penyelesaian sisa waktu
            tsisa_act  = (tFOG_berakhir-tnow).total_seconds()
            act_durasi = used_durasi
            # HITUNG sisa waktu AKTUATOR
            if (used_durasi>0):
                # selama aktuator ON, tidak boleh ada perintah PUB
                if (foggingON==True and kipasON==True): izinActs ='Close'; izinAct[0]=0
                
                if (tsisa_act>0):
                    ts_actj = tFOG_berakhir - tnow
                    txtsisa=f"{ts_actj}"
                    txtsisb=f"{tFOG_berakhir-tFOG_mulai}"
                    u_dura = f'{act_durasi} dtk'
                elif (JEDA_ANTAR_PUB+tsisa_act)>0:
                    # HITUNG sisa waktu jeda antar pubikasi
                    ts_actj = (tFOG_berakhir + timedelta(seconds=JEDA_ANTAR_PUB)) - tnow
                    txtsisa = f"{ts_actj}"
                    txtsisb = f"jeda/tunggu"
                    act_durasi=0
                    u_dura = f'{act_durasi} dtk'
                else:
                    # aktifkan status izin ACT: perintah fogging/kipas
                    # nanti di-crosscek dengan data subscribe dari fogging
                    foggingON=False;                      data_fogging='00000'
                    kipasON  =False;                      data_kipas  ='00000'
                    izinActs ='OPEN';                     izinAct[0]=1
                    used_durasi=act_durasi=durasi_fogging=durasi_kipas = 0
                    txtsisa=txtsisb='-'
                    txt_headL = 'PERHITUNGAN'
                    u_dtma = u_durt = u_dura = srh = stwb = '-'
            
            # tampilkan hasil analisis/perhitungan yang digunakan
            ### MASIH di dalam nested #3 -- save hasil
            # save file DATA hasil: waktu, suhu rata2, rh rata2 status kip/fog
            waktu = mi.waktu_str()
            namafile = osft.prepDir("Data_hasil","Waktu;sesi_ke;prosesON;massa_air;suhu_input;suhu_rata;suhu_movavg;rh_rata;rh_movavg;data_Kipas;durasi_kipas;data_Fogging;durasi_Fogging\n")
            data_hasil=f"{waktu};{c};{prosesON};{round(used_deltama,2)};{round(t1,2)};{tRata};{tMov};{rhRata};{rhMov};{data_kipas};{int(durasi_kipas)};{data_fogging};{int(durasi_fogging)}"
            osft.save_csv(namafile, data_hasil)
            logprint.append(f'[] HSL: {data_hasil}')
            print("=================================================")        
            print (txt_headL)
            print (f"twb                      : {stwb}")
            print (f"rh                       : {srh}")
            print (f"estimasi uap air tambahan: {u_dtma}")
            print (f"lama waktu fogging       : {u_durt}")
            print (f"durasi (aktif)           : {u_dura}")
            ### END nested #3 -- 
            
        ### END nested #2
        # [ AKTUATOR ]
        print("=================================================")   
        print ("[ AKTUATOR ]")
        print (f"Fogging ON      : {foggingON}")
        print (f"Kipas ON        : {kipasON}")      
        print (f"Status aktuator : {izinActs}")  
        print (f"Lama waktu      : {txtsisb}")
        print (f"Sisa waktu      : {txtsisa}")
    
        
        # update respon GPIO aktuator
        if stAct_gpio[5][2]==data_kipas:   responKIP='ON '
        if stAct_gpio[5][3]=='00000':    responKIP='OFF'
        if stAct_gpio[6][2]==data_fogging: responFOG='ON '
        if stAct_gpio[6][3]=='00000':     responFOG='OFF'
        if (stAct_gpio[5][3]=='00000' and stAct_gpio[6][3]=='00000' and izinActs=='OPEN'):
            stAct_gpio={6:['','','',''],5:['','','','']}
            responFOG=responKIP='-  '
 
           
    tnow = datetime.now()
    print (f"Respon fogging :{responFOG}")
    print (f"Respon kipas   :{responKIP}")  
    # publikasi data display 02
    dispFOG=responFOG;            dispKIP=responKIP;        cK=str(c)
    if dispFOG !='ON ': dispFOG='OFF'
    if dispKIP !='ON ': dispKIP='OFF'
    if tKondusif==True: cK=cK+'*'
    wkt=mi.waktu_str().replace(" ","_")
    payload_str=f"{kode_client};{tMov};{rhMov};{dispFOG};{dispKIP};{round(used_deltama,2)};{round(act_durasi/60,2)};{cK};{wkt}"
    payload_str=payload_str.replace(" ",'')
    publikasi_pesan(broker,client,topik_disp02, payload_str)
    pr_info.append(f'-> data display 02: [ {payload_str} ]')
    print(f"-> data display 02: [{payload_str}]")
    # save display ke file txt
    os.system(f"echo '{payload_str}' > /home/pi/Documents/program_model_gh/txt/LOG_display02.txt")

    # cek sub_dts
    sub_dts, txtpesan, data_warning = msc.cek_masa_sub_terakhir(sub_dt, limit_sub)
    # pencatatan kondisi warning:
    if data_warning!='-':
        waktu_now=mi.waktu_str()
        namafile = osft.prepDir("Data_warningSUB","Waktu;sesi_ke;prosesON;t_subwarn1;t_subwarn2;t_subwarn3;no_client;Info\n")
        osft.save_csv(namafile, f"{waktu_now[11:]};{c};{prosesON};{data_warning}")
        
        if txtpesan != '-': (txtpesan,'ki')   
    else:
        txclear=(f"                                                                                                                    ")
        print(txclear)
          
    ts_sub = max(sub_dts)
    if c>1:
        #tx_sub = f'-> masa sub terakhir (per client TRH): {sub_dts} / paling lama: {ts_sub}'
        print(f"Masa sub terakhir: dari tiap client")
        print(f"Sub terlama: {ts_sub} detik")
    
    # cek indikasi_error
    # update status client, dari status FIX
    # sud include di indikasi -- msc.cek_statusFIX()
    txtpesan, txtwarning=msc.cek_indikasi_error()
    if txtpesan  !='-':         pr_info.append(txtpesan)
    if txtwarning!='-':         (txtwarning,'ki')
    else:
        txclear=(f"                                                                                                                    ")
        print({txclear})   
        
    if ts_sub > limit_sub-30:  
        pr_info.append(f"-> program akan RESTART, bila lebih dari {limit_sub} dtk ")
        print(f"-> program akan RESTART, bila lebih dari {limit_sub} detik ")
        if (ts_sub>limit_sub and foggingON==kipasON):
            tx_sub=''
            st_RST = msc.RW_1barisTXT('var_statRST3_client.txt',0,'-')
            for i in range(len(sub_dt)): 
                if sub_dts[i]==ts_sub:      tx_sub=tx_sub+str(st_RST[i]+1)
                else:                       tx_sub=tx_sub+str(st_RST[i])
            os.system(f'echo {tx_sub} > /home/pi/Documents/program_model_gh/var_statRST3_client.txt')
            txtpesan=(f">> *   PROGRAM DI RESTART-SUB (py)   * <<")
            (txtpesan,'ki')
        
            osft.restartPROG('SUB');        dloop=False;        exit()
    
    # pengecekan JADWAL restart/reboot
    if tnow>=sLimit + timedelta(hours=-1):
        # info muncul 1 jam sebelumnya
        pr_info.append(f'-> {sLimit-tnow} menuju jadwal restart: {sLimit}')
        print(f"->{sLimit-tnow} menuju jadwal restart: {sLimit}")
        txtpesan="                                                                             "
    if (tnow>=sLimit and foggingON==kipasON):                          # jadwal sudah terlampaui

        txtpesan=(f">> *   PROGRAM DI RESTART-{sorder} (py)   * <<")
        (txtpesan,'ki')
        
        #scr.refresh();     time.sleep(5);      curses.curs_set(1);      curses.endwin()

        if sorder=='RB':           osft.restartPROG('RBT')       # reboot
        if sorder=='RS':           osft.restartPROG('RTN')       # restart
        dloop=False;
        exit();   
         
    # cetak info2 dan log2
    #### save to txt untuk ke WEB

    waktu_now=mi.waktu_str()
    web_txt = f"{waktu_now[11:]}$"
    for i in range(0,len(logprint)):       
        tx=f"{logprint[i][3:]}$"
        tx=tx.replace("#",'')
        web_txt=web_txt+tx
    web_txt=web_txt+"$"
    for i in range(0,len(pr_info)):        
        tx=f"{pr_info[i][3:]}$"
        tx=tx.replace("#",'')
        web_txt=web_txt+tx
        
    #os.system(f"echo 'data_pedca' > /home/pi/txt/web_printext.txt")
    #os.system(f"echo '{web_txt}' >> /home/pi/txt/web_printext.txt")
    
    time.sleep(JEDA_PENGUKURAN)
    
 # LOG DITAMPILKAN TERAKHIR, SUPAYA SEMUA DATA LOG MUNCUL (kalo lebih dulu dibanding info, sub tidak muncul)
    pr_info=[]
    logprint=[]

   # kirim pesan untuk UPDATE waktu client setiap jam ke DISPLAY02
    tupd = datetime.now()
    str_tupd = tupd.strftime('%Y-%m-%d %H:%M:%S')
    if jH != tupd.strftime('%H'):
        payload_str=kode_client+";update_time;"+str_tupd+";"+str(c)
        #topik_pub = [topik_fogging, topik_kipas, topik_dtime, topik_disp02, topik_maintain]
        #for t in range(len(topik_pub)): --> untuk ke semua client
        publikasi_pesan(broker,client, topik_disp02, payload_str)
        jH = tupd.strftime('%H')
        
### end

