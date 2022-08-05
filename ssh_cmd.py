import paramiko

def ssh_command(ip,port,passed,passwd,cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect(ip,port=port,username=user,password=passwd)

    _,stdout,stderr = client.exec_command(cmd)
    output = stdout.readlines()+stderr.readlines()
    if output:
        print('output')
        for line in output:
            print(line.strip())

if __name__ == '__main__':
    import  getpass
    user = input('username:')
    password = getpass.getpass()

    ip = input('enter server ip:') or '192.168.1.203'
    port = input('enter port or <CR>:') or 2222
    cmd = input('enter command or <CR>:') or 'id'
    ssh_command(ip,port,user,password,cmd)