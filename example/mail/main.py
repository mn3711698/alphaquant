import poplib, os.path, mimetypes

from email.parser import BytesParser, Parser

from email.policy import default

# 输入邮件地址, 口令和POP3服务器地址:
err=\xb5\xc7\xc2\xbc\xcc\xab\xc6\xb5\xb7\xb1!\xc7\xeb\xbc\xec\xb2\xe9\xc4\xfa\xb5\xc4outlook,foxmail\xbb\xf2\xd5\xdf\xc6\xe4\xcb\xfc\xd7\xd4\xb6\xaf\xbc\xec\xb2\xe2\xd3\xca\xcf\xe4\xb5\xc4\xb9\xa4\xbe\xdf(\xc0\xfd\xc8\xe7\xcd\xf8\xd2\xd7popo\xb5\xc8\xc1\xc4\xcc\xec\xb9\xa4\xbe\xdf),\xbd\xab\xbc\xec\xb2\xe2\xb5\xc4\xca\xb1\xbc\xe4\xbc\xe4\xb8\xf4\xb5\xf7\xb4\xf3\xd2\xbb\xd0\xa9\xa3\xac\xc0\xfd\xc8\xe75\xb7\xd6\xd6\xd3\xbc\xe0\xb2\xe2\xd2\xbb\xb4\xce
err=BytesParser(policy=default).parsebytes(err)
print(err)
email = 'chemozhici@126.com'

password = 'rtqt576533'

pop3_server = 'pop.126.com'

# 连接到POP 3服务器:

# conn = poplib.POP3(pop3_server, 110)

conn = poplib.POP3_SSL(pop3_server, 995)

# 可以打开或关闭调试信息:

conn.set_debuglevel(1)

# 可选:打印POP 3服务器的欢迎文字:

print(conn.getwelcome().decode('utf-8'))

# 输入用户名、密码信息

# 相当于发送POP 3的user命令

conn.user(email)

# 相当于发送POP 3的pass命令
try:
    conn.pass_(password)
except Exception as e:
    msg=BytesParser(policy=default).parsebytes(e)
    print(msg)
# 获取邮件统计信息，相当于发送POP 3的stat命令

message_num, total_size = conn.stat()

print('邮件数: %s. 总大小: %s' % (message_num, total_size))

# 获取服务器上的邮件列表，相当于发送POP 3的list命令

# resp保存服务器的响应码

# mails列表保存每封邮件的编号、大小

resp, mails, octets = conn.list()

print(resp, mails)

# 获取指定邮件的内容（此处传入总长度，也就是获取最后一封邮件）

# 相当于发送POP 3的retr命令

# resp保存服务器的响应码

# data保存该邮件的内容
def parse(msg):
    for part in msg.walk():
        counter = 1
        # 如果maintype是multipart，说明是容器（用于包含正文、附件等）
        if part.get_content_maintype() == 'multipart':
            continue
        # 如果maintype是multipart，说明是邮件正文部分
        elif part.get_content_maintype() == 'text':
            print(part.get_content())
        # 处理附件
        else:
            # 获取附件的文件名
            filename = part.get_filename()
            # 如果没有文件名，程序要负责为附件生成文件名
            if not filename:
                # 根据附件的contnet_type来推测它的后缀名
                ext = mimetypes.guess_extension(part.get_content_type())
                # 如果推测不出后缀名
                if not ext:
                    # 使用.bin作为后缀名
                    ext = '.bin'
                # 程序为附件来生成文件名
                filename = 'part-%03d%s' % (counter, ext)
            counter += 1
            # 将附件写入的本地文件
            with open(os.path.join('.', filename), 'wb') as fp:
                fp.write(part.get_payload(decode=True))


for i in range(1,len(mails)):
    resp, data, octets = conn.retr(i)
    # 将data的所有数据（原本是一个字节列表）拼接在一起
    msg_data = b'\r\n'.join(data)
    # 将字符串内容解析成邮件，此处一定要指定policy=default
    msg = BytesParser(policy=default).parsebytes(msg_data)  # ①
    print(type(msg))
    print('发件人:' + msg['from'])
    print('收件人:' + msg['to'])
    print('主题:' + msg['subject'])
    print('第一个收件人名字:' + msg['to'].addresses[0].username)
    print('第一个发件人名字:' + msg['from'].addresses[0].username)
    parse(msg)


# 退出服务器，相当于发送POP 3的quit命令
conn.quit()