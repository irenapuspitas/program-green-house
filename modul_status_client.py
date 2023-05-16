from datetime import datetime, timedelta
import modul_iot as mi
import os

def R_nomor_clientTRH():
    # nama file
    nf=txfolder="E:/Program model gh/TRH_nomor_client.txt"

    # baca data fix (isi manual) status client
    with open(f"{nf}") as f:
        for line in f: isi_list=list(line[:len(line)-1])
        isi_list=[int(i) for i in  isi_list]
        f.close()
    return isi_list

def RW_1barisTXT(nf,mode,isi):
    # mode 0=read,1=write

    #st_RST   =RW_1barisTXT('var_statRST3_client.txt',0,'-')     # baca jumlah even restart berturut turut
    #if isi=='-': isi_list=[0,0,0]
    isi_list=[0,0,0]            # inisiasi
    txfolder="E:/Program model gh"

    if mode==0:
        # baca data fix (isi manual) status client
        with open(f"{txfolder}/{nf}") as f:
            for line in f: isi_list=list(line[:3])
            isi_list=[int(i) for i in  isi_list]
            f.close()
    if mode==1:
        # write echo
        isi_list=[str(i) for i in isi];              j="".join(isi_list)
        os.system(f"echo {j} > {txfolder}/{nf}")

    return isi_list

def cek_indikasi_error():
    txpesan=txwarn='-'
    # tampilkan indikasi ERROR

    st_FIX      = RW_1barisTXT('fix_statclient_ERR.txt',0,'-')      # baca ERROR fix manual
    st_CLI      = RW_1barisTXT('var_statclient_ERR.txt',0,'-')      # baca status client
    st_RST      = RW_1barisTXT('var_statRST3_client.txt',0,'-')     # baca jumlah even restart berturut turut
    st_NOL      = RW_1barisTXT('var_statNOL9_client.txt',0,'-')     # baca jumlah data NOL masuk berturut turut

    # update nilai status terhadap fix nya
    for i in range(len(st_FIX)):
        if st_FIX[i]==1: st_CLI[i] = 1

    # update nilai file status
    RW_1barisTXT('var_statclient_ERR.txt',1,st_CLI)       # update ERROR proses

    if (max(st_RST)>0 or max(st_NOL)>0 or max(st_CLI)>0):
            txpesan=(f'-> indikasi client TRH ERROR: RST {st_RST} / NOL {st_NOL} / ERR {st_CLI}')

    nomorclient_ERR=''
    for i in range(len(st_CLI)):
        if st_CLI[i] == 1: nomorclient_ERR=nomorclient_ERR + str(i+1) + ' '

    if nomorclient_ERR !='':    txwarn=(f" >> client TRH ke: [ {nomorclient_ERR}] TIDAK BERFUNGSI << ")

    #print(txwarn, txpesan)
    return  txpesan, txwarn

def cek_masa_sub_terakhir(subdt, tlimit):
    # cek lama sub masuk, jika > 60 detik, data di NOL kan
    # menampilkan lama jeda SUB terakhir yang diterima
    # perhitungan waktu sub, hanya pada client normal (yang rusak diabaikan)
    tN = datetime.now()
    subdts=[0,0,0]

    # cek client error, NOL-kan sub_dts bila erro
    st_CLI      = RW_1barisTXT('var_statclient_ERR.txt',0,'-')      # baca status client

    dt_warn='-'
    scr_pesan=(f"-")

    for i in range(len(subdt)):
        if st_CLI[i]==1:
            subdts[i]=0
        else:
            subdts[i]=int((tN-subdt[i]).total_seconds())

        if subdts[i] > tlimit-60:
            sinfo = f"{i+1}, TIDAK muncul ({subdts[i]})"
            if subdts[i]>tlimit: sinfo = sinfo + ' <- RESTART'
            scr_pesan=(f" [WARNING]: client TRH: {sinfo} ")

            dt_warn=f"{subdts[0]};{subdts[1]};{subdts[2]};{sinfo}"

    return subdts, scr_pesan, dt_warn

def update_status_CLI(dat):
    # proses data client TRH NO, untuk indikasi rusak

    client_TRH=[1,2,3]
    limitNOL_rusak=9            # 10x dari NOL
    #limitRST_rusak=3

    # 1 read dulu, nilai2 variabel txt
    st_CLI   =RW_1barisTXT('var_statclient_ERR.txt',0,'-')      # baca ERROR proses terakhir
    st_RST   =RW_1barisTXT('var_statRST3_client.txt',0,'-')     # baca jumlah even restart berturut turut
    st_NOL   =RW_1barisTXT('var_statNOL9_client.txt',0,'-')     # baca jumlah data NOL masuk berturut turut

    # 2 cek RST limit
    for i in range(len(st_RST)):
        if st_RST[i]>=3: st_CLI[i]=1
        #if st_RST[i]< 3: st_CLI[i]=0

    # 3 olah data
    if len(dat)>3:
        k=mi.parsing4(dat)
        ns=int(mi.baca_no_client(k[0])) # nomor stasiun
        if ns in client_TRH:
            if dat.find(';0;0;0;0;')>=0:
                if   st_NOL[ns-1]< limitNOL_rusak:          st_NOL[ns-1]=st_NOL[ns-1]+1
                elif st_NOL[ns-1]>=limitNOL_rusak:          st_CLI[ns-1]=1
            elif dat.find(';0;0;0;0;')<0:
                st_NOL[ns-1]=0;
                st_RST[ns-1]=0;
                st_CLI[ns-1]=0

    # 4 write UPDATE
    RW_1barisTXT('var_statclient_ERR.txt',1,st_CLI)       # update var status CLI
    RW_1barisTXT('var_statNOL9_client.txt',1,st_NOL)      # update data nol proses
    RW_1barisTXT('var_statRST3_client.txt',1,st_RST)      # update restart proses

def cek_selisih_data(sh0,rh0,rtsh,rtrh):
    # tidak dipake dulu, takut error
    dsh=0; drh=0; tsh_pesan=trh_pesan=txpesan='-'
    for i in range(len(sh0)):
        if abs(sh0[i]-rtsh)>=dsh: dsh=abs(sh0[i]-rtsh); tsh_pesan=f' SUHU [ {round(dsh,2)} / {sh0[i]} ]'
        if abs(rh0[i]-rtrh)>=drh:  drh=abs(rh0[i]-rtrh);  trh_pesan=f' RH [ {round(drh,2)} / {rh0[i]} ]    '

    txpesan = (f'-> selisih terbesar (dari rata2) : {tsh_pesan} / {trh_pesan}')
    return txpesan

