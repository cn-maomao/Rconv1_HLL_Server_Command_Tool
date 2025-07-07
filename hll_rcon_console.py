# 导入所需的库
import socket  # 用于网络连接
import time    # 用于添加延迟
import os      # 用于访问环境变量
from dotenv import load_dotenv  # 用于从 .env 文件加载环境变量

# 从 .env 文件加载环境变量（如果存在）
# 这允许我们将敏感信息（如密码）与代码分开存放
load_dotenv()

class XOR_RCON:
    """
    处理与 HLL RCON 服务器的连接、加密和通信的类。
    HLL RCON 使用 XOR 加密来保护通信。
    """
    def __init__(self, host, port, password, timeout=10):
        """
        初始化 RCON 客户端。
        :param host: 服务器 IP 地址
        :param port: 服务器 RCON 端口
        :param password: RCON 密码
        :param timeout: 网络操作的超时时间（秒）
        """
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.socket = None  # 用于存储 socket 连接对象
        self.xor_key = None # 用于存储从服务器接收的 XOR 加密密钥

    def connect(self):
        """建立 TCP 连接并从服务器获取 XOR 密钥。"""
        # 创建一个 TCP/IP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置 socket 操作的超时时间
        self.socket.settimeout(self.timeout)
        # 连接到服务器
        self.socket.connect((self.host, self.port))
        # 建立连接后，服务器会立即发送 XOR 密钥
        self.xor_key = self.socket.recv(4096)
        # 打印连接成功信息和接收到的密钥（以十六进制格式）
        print(f"Connected. Received XOR key: {self.xor_key.hex()}")

    def xor_crypt(self, data):
        """使用密钥对数据进行 XOR 加密或解密。"""
        # 如果尚未收到密钥，则无法进行加密/解密
        if not self.xor_key:
            raise ValueError("XOR key not received yet.")
        # 如果数据是字符串，先将其编码为 UTF-8 字节
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        key_len = len(self.xor_key)
        # 使用密钥对数据中的每个字节执行 XOR 操作
        # 如果数据比密钥长，密钥会重复使用
        return bytes(a ^ b for a, b in zip(data, self.xor_key * (len(data) // key_len + 1)))

    def send(self, command):
        """将经过 XOR 加密的命令发送到服务器。"""
        # 使用 xor_crypt 方法加密命令
        encrypted_command = self.xor_crypt(command)
        # 打印原始命令和加密后的命令（以十六进制格式），用于调试
        print(f"Sending: '{command}' | Encrypted: {encrypted_command.hex()}")
        # 发送加密后的命令
        self.socket.send(encrypted_command)
        # 发送后立即等待并接收服务器的响应
        return self.receive()

    def receive(self):
        """从服务器接收并解密响应。"""
        # 从 socket 接收原始（加密的）数据
        raw_response = self.socket.recv(4096)
        # 打印原始响应（以十六进制格式），用于调试
        if not raw_response:
            return ""
        # 使用相同的 xor_crypt 方法解密响应
        decrypted_response = self.xor_crypt(raw_response)
        # 将解密的字节解码为 UTF-8 字符串并返回，忽略任何解码错误
        return decrypted_response.decode('utf-8', errors='ignore')

    def close(self):
        """关闭网络连接。"""
        if self.socket:
            self.socket.close()
            print("Connection closed.")

def display_help():
    """显示基于 HLL RCON 官方文档的可用命令列表。"""
    # 这个多行字符串包含了所有支持的命令及其简要说明
    commands = """
Available Commands (case-insensitive):
    !所有参数之间使用空格分割,< >为必填参数,[ ]为可选参数!
    !所有参数无需< >与[ ],若参数含有空格需加上英文双引号" "!
    !所有服务器登陆RCON密码即可使用所有命令,请注意安全!
    !on=开启,off=关闭!
    !根据Github项目作者2KU77B0N3S修改!
    !汉化、添加注释与支持多服务器配置 by猫猫酱!
    !https://github.com/cn-maomao/HLL_Server_Command_Tool!
  通用:
    help                              - 显示所有服务器命令
    Login <password>                  - 登陆连接
    RconPassword <old> <new>          - 更改RCON密码(高危操作)

  服务器:
    Get Name                         - 获取当前服务器名称
    Get Slots                        - 获取在线人数和最大玩家人数
    Get GameState                    - 获取对局信息
    Get MaxQueuedPlayers             - 获取排队队列数量
    Get NumVipSlots                  - 获取VIP预留位
    SetMaxQueuedPlayers <数量>       - 设置排队队列
    SetNumVipSlots <数量>          - 设置VIP预留位
    Say <内容>                    - 设置弹窗消息(游戏左上角弹窗)
    Broadcast <内容>              - 设置服务器公告栏内容(值空则清楚内容)
    ShowLog <多久分钟之前> ["关键词"]    - 获取多久前的日志      - 发送指令ShowLog 5 chat 则显示5分钟前与chat有关的日记

  地图:
    Get Map                          - 获取当前地图
    Get MapsForRotation              - 列出所有可用地图
    Get ObjectiveRow_[0-4]           - 列出当前地图单个点位的名称(第一点=0、第二点=1......第五点=4)   - 发送指令Get ObjectiveRow_1 则回复当前地图第二点的所有点位名称
    RotList                          - 获取下一张轮换图
    RotAdd <地图名称> [位置]   - 将地图添加到图池中      -建议直接游戏服务器后台编辑Map文件,而不是使用代码
    RotDel <地图名称>      - 从图池中删除地图
    Map <地图名称>             - 切换当前地图
    GameLayout <obj0> <obj1> <obj2> <obj3> <obj4>    - 以指定地图点位重新切图   - 需要通过Get ObjectiveRow命令查看点位名称(第一点=0、第二点=1......第五点=4)
    QueryMapShuffle                  - 检查是否启用随机地图
    ToggleMapShuffle                 - 开启/关闭随机地图
    ListCurrentMapSequence           - 显示当前服务器地图图池

  Players:
    Get Players                      - 显示在线玩家信息
    Get PlayerIds                    - 显示在线玩家uid
    Get AdminIds                     - 获取所有管理员的列表,包括备注、UID 和 权限
    Get AdminGroups                  - 显示所有管理员权限分组
    Get VipIds                       - 显示VIP,包括uid与备注
    PlayerInfo <"玩家名称">                - 返回详细的玩家信息,包括团队、单位、角色和击杀数(部分信息仅限在线状态显示)
    AdminAdd <"uid"> <"权限"> ["备注"] - 添加管理员
    AdminDel <uid>                   - 删除管理员
    VipAdd <"uid"> <"备注">          - 添加VIP
    VipDel <uid>                     - 删除VIP

  Moderation:
    Get TempBans                     - 显示临时封禁(包括投票踢出,2小时封禁等任何非永久的临时封禁)
    Get PermaBans                    - 显示永久封禁(仅包括存储在游戏服务器文件内的永久封禁,不包括例如BM面板等第三方插件的封禁)
    Message <"玩家uid或全称"> <"内容">   - 私信玩家管理员信息
    Punish <"玩家uid或全称"> ["原因"]     - 击杀玩家
    SwitchTeamOnDeath <玩家uid或全称>       - 死后调边
    SwitchTeamNow <玩家uid或全称>           - 立即调边
    Kick <"玩家uid或全称"> ["原因"]       - 踢出服务器
    TempBan <"uid"> [时间(小时)] ["原因"] ["操作人员"] - 服务器临时封禁
    PermaBan <"uid"> ["原因"] ["操作人员"] - 服务器永久封禁(不推荐使用)
    PardonTempBan <uid>          - 解除临时封禁
    PardonPermaPan <uid>         - 解除永久封禁 (仅支持存储在游戏服务器文件内的永久封禁,不包括例如BM面板等第三方插件的封禁)

  Configuration:
    Get Idletime                     - 获取空闲踢出时间
    Get HighPing                     - 获取最高Ping值
    Get TeamSwitchCooldown           - 获取团队玩家自行调边冷却
    Get AutoBalanceEnabled           - 显示人数平衡状态
    Get AutoBalanceThreshold         - 显示多少人自动开启人数平衡
    Get VoteKickEnabled              - 显示玩家投票踢人状态
    Get VoteKickThreshold            - 更改玩家投票踢人比例
    Get Profanity                    - 显示违禁词
    SetKickIdleTime <时间(分钟)>        - 设置空闲踢出时间
    SetHighPing <ms>                 - 设置最高Ping值
    SetTeamSwitchCooldown <时间(分钟)>  - 设置团队玩家自行调边冷却
    SetAutoBalanceEnabled <on/off>   - 设置显示人数平衡
    SetAutoBalanceThreshold <数量>    - 设置多少人自动开启人数平衡
    SetVoteKickEnabled <on/off>      - 设置是否启用玩家投票踢出
    SetVoteKickThreshold <pairs>     - 设置投票踢人比例(例如"25,10")
    ResetVoteKickThreshold           - 重置投票踢人比例
    BanProfanity <word1,word2>       - 添加违禁词(英文逗号分隔)
    UnbanProfanity <words>           - 删除违禁词(英文逗号分隔)

  Extra:
    exit                             - 关闭连接并退出
    switch                           - 断开连接并返回服务器选择
    """
    print(commands)

def load_servers():
    """从环境变量加载所有服务器配置。"""
    servers = []
    i = 1
    while True:
        name = os.getenv(f"SERVER_{i}_NAME")
        host = os.getenv(f"SERVER_{i}_HOST")
        port = os.getenv(f"SERVER_{i}_PORT")
        password = os.getenv(f"SERVER_{i}_PASSWORD")

        if not all([name, host, port, password]):
            break  # 如果缺少任何一个必需的变量，则停止搜索

        try:
            port = int(port)
            servers.append({"name": name, "host": host, "port": port, "password": password})
        except ValueError:
            print(f"Warning: Skipping server {i} due to invalid port: {port}")
        
        i += 1
    return servers

def select_server(servers):
    """显示服务器列表并让用户选择一个。"""
    print("请选择要连接的服务器:")
    for i, server in enumerate(servers):
        print(f"  {i + 1}: {server['name']} ({server['host']}:{server['port']})")
    
    while True:
        try:
            choice = input("请输入服务器序号 (或输入 'q' 退出): ").strip()
            if choice.lower() == 'q':
                return None
            choice_num = int(choice)
            if 1 <= choice_num <= len(servers):
                return servers[choice_num - 1]
            else:
                print("无效的序号，请重试。")
        except ValueError:
            print("无效输入，请输入数字。")

def start_rcon_session(server_config):
    """为一个选定的服务器启动 RCON 会话。"""
    rcon = XOR_RCON(
        host=server_config['host'],
        port=server_config['port'],
        password=server_config['password']
    )
    try:
        print(f"\n正在连接到 {server_config['name']}...")
        rcon.connect()

        login_response = rcon.send(f"Login {rcon.password}")
        print(f"登录响应: '{login_response}'")

        if "SUCCESS" not in login_response:
            print("登录失败。请检查您的密码和服务器状态。")
            time.sleep(2) # Pause to let user read the message
            return

        print("登录成功。输入 'help' 查看命令，'switch' 切换服务器，或 'exit' 退出。")
        time.sleep(1)

        while True:
            command = input(f"({server_config['name']}) > ").strip()
            if not command:
                continue
            
            cmd_lower = command.lower()
            if cmd_lower == "exit":
                # 'exit' will be caught by the outer loop to terminate the program
                return "exit"
            elif cmd_lower == "switch":
                print("正在断开当前服务器...")
                return # Return to server selection
            elif cmd_lower == "help":
                display_help()
            else:
                response = rcon.send(command)
                print(f"响应: '{response}'")

    except Exception as e:
        print(f"\n错误: {e}")
        print("正在返回服务器选择界面...")
        time.sleep(2)
    finally:
        rcon.close()

def main():
    """程序的主函数，处理服务器选择和会话管理。"""
    servers = load_servers()
    if not servers:
        print("错误：未配置服务器。请检查您的 .env 文件。")
        print("文件中应包含类似 SERVER_1_NAME, SERVER_1_HOST 等连续的服务器定义。")
        return

    while True:
        selected_server = select_server(servers)
        if selected_server is None:
            print("正在退出。")
            break
        
        result = start_rcon_session(selected_server)
        if result == "exit":
            print("正在退出。")
            break

if __name__ == "__main__":
    main()
