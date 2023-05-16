import os
import time
from datetime import datetime, timedelta

# Function preparing file and directory

def prepDir(n, txh):
    #nf: nama file -->  depannya saja : akan ditambah tanggal hari ini, setiap hari ganti file

    #path0 = "~/Documents/csv"
    date = datetime.now().strftime('%Y-%m-%d')
    #_t = time.time()

    nama_file = f"{n}_{date}.csv"
    #nama_folder=path0 # dalam satu folder dengan program
    nama_folder=f"{os.getcwd()}/csv" # dalam satu folder dengan program
    nama_file_lengkap=nama_folder + '/' + nama_file # chr(92)='\'

    #pathData = '/home/pi/csv/' + folder
    #fullPath = pathData + fileName
    if not os.path.exists(nama_folder):
        #creating new folder
        os.makedirs(nama_folder)

    #creating header in CSV file
    # tulis judul kolom bila file belum ada
    # atau bila pertama kali membuat file. Untuk pengisian data
    # selanjutnya bagian ini akan diabaikan
    if not os.path.exists(nama_file_lengkap):
        # print('\n[] Nama file:',nama_file_lengkap)
        with open(nama_file_lengkap, 'w') as file1:  # mode penulisan (write)
            # katakunci newline: menambahkan string kosong untuk baris baru
            # sehingga untuk data berikutnya akan secara otomatis
            # diletakkan pada baris baru

            #txheader=txh    #"Waktu;ClientID;data1;data2;data3;data4;no_urut\n"
            file1.write(txh)
            file1.close()
    return nama_file_lengkap

def save_csv(nf,d):
    # d: data, isian data yng disimpan
    fullPath = nf
    # print("nama file lengkap: ",fullPath)
    with open(fullPath, "a") as file1: # mode penambahan (append)
        #output="Waktu;ClientID;data1;data2;data3;data4;no_urut\n"
        file1.write(f"{d}\n")
        file1.close()

def setLIMIT():
    #RS: reSTART program python
    #RB: reBOOT  mesin pc/raspi

    tN = datetime.now()
    #tN.strftime('%Y%m%d')

    jam00  = datetime(tN.year, tN.month, tN.day, 0, 0, 0, 0)
    jam02  = jam00  + timedelta(hours=2)
    jam05  = jam00  + timedelta(hours=5)
    jam16  = jam00  + timedelta(hours=15, minutes=50)       #buat tes program
    jam18  = jam00  + timedelta(hours=18)
    jam24  = jam00  + timedelta(hours=24, seconds=10)

    if tN <= jam02:              dLIMIT = jam02;        	      order='RB' #di jam2
    elif tN <= jam05:            dLIMIT = jam05;        	      order='RS' #di jam5
    #elif tN <= jam16:            dLIMIT = jam16;        	      order='RB' #di jam16
    elif tN <= jam18:            dLIMIT = jam18;        	      order='RS' #di jam18
    else:                        dLIMIT = jam24;     	      order='RS' #di jam24 10detik
    return dLIMIT,order

def restartPROG(jn):
    txjn = jn
    if jn=='SUB':    txjn = 'SUB tidak masuk'
    if jn=='RTN':    txjn = 'terjadwal'
    if jn=='RBT':    txjn = 'terjadwal'

    if txjn=='terjadwal':
        os.system(f'echo 000 > /home/pi/txt/var_statclient_ERR.txt')         # inisiasi var status sub client
        os.system(f'echo 000 > /home/pi/txt/var_statRST3_client.txt')        # inisiasi var status reset
        os.system(f'echo 000 > /home/pi/txt/var_statNOL9_client.txt')        # inisiasi var status data nol

    txfile=f"/home/pi/txt/{datetime.now().strftime('%Y%m')}_log_boot.txt"
    if jn=='RBT':
        os.system(f"echo {datetime.now()} / REBOOT: {txjn} >> {txfile}")
        os.system("reboot")

    else:
        os.system(f"echo {datetime.now()} / RESTART: {txjn} >> {txfile}")
        #os.system(f"python3 /home/pi/Documents/START_program_00.py")
        os.system(f"mate-terminal -e /home/pi/shrun/start00.sh")

    time.sleep(2)
