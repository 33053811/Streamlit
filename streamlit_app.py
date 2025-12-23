import os
2	+
import sys
3	+
import subprocess
4	+
import time
5	+
import signal
6	+
from pathlib import Path
7	+
import requests
8	+
from datetime import datetime
9	+
import streamlit as st
10	+
import tarfile
11	+
import io
12	+
13	+
# 配置
14	+
TMATE_VERSION = "2.4.0"  # 使用最新稳定版本
15	+
TMATE_DOWNLOAD_URL = f"https://github.com/tmate-io/tmate/releases/download/{TMATE_VERSION}/tmate-{TMATE_VERSION}-static-linux-amd64.tar.xz"
16	+
USER_HOME = Path.home()
17	+
SSH_INFO_FILE = "/tmp/ssh.txt"  # 保存到临时目录
18	+
19	+
class TmateManager:
20	+
    def __init__(self):
21	+
        self.tmate_dir = USER_HOME / "tmate"
22	+
        self.tmate_path = self.tmate_dir / "tmate"
23	+
        self.ssh_info_path = Path(SSH_INFO_FILE)
24	+
        self.tmate_process = None
25	+
        self.session_info = {}
26	+
        
27	+
    def download_tmate(self):
28	+
        """从官方GitHub下载并安装tmate"""
29	+
        st.info("正在下载并安装tmate...")
30	+
        
31	+
        # 创建tmate目录
32	+
        self.tmate_dir.mkdir(exist_ok=True)
33	+
        
34	+
        try:
35	+
            # 下载tmate压缩包
36	+
            response = requests.get(TMATE_DOWNLOAD_URL, stream=True)
37	+
            response.raise_for_status()
38	+
            
39	+
            # 使用内存中的字节流处理压缩包
40	+
            with io.BytesIO(response.content) as tar_stream:
41	+
                # 使用tarfile解压
42	+
                with tarfile.open(fileobj=tar_stream, mode="r:xz") as tar:
43	+
                    # 提取tmate二进制文件
44	+
                    tar.extract("tmate-2.4.0-static-linux-amd64/tmate", path=str(self.tmate_dir))
45	+
            
46	+
            # 重命名并设置权限
47	+
            extracted_path = self.tmate_dir / "tmate-2.4.0-static-linux-amd64" / "tmate"
48	+
            if extracted_path.exists():
49	+
                extracted_path.rename(self.tmate_path)
50	+
                os.chmod(self.tmate_path, 0o755)
51	+
            
52	+
            # 清理临时目录
53	+
            subprocess.run(["rm", "-rf", str(self.tmate_dir / "tmate-2.4.0-static-linux-amd64")])
54	+
            
55	+
            # 验证安装
56	+
            if self.tmate_path.exists() and os.access(self.tmate_path, os.X_OK):
57	+
                st.success(f"✓ tmate已安装到: {self.tmate_path}")
58	+
                return True
59	+
            else:
60	+
                st.error("✗ tmate安装失败")
61	+
                return False
62	+
            
63	+
        except Exception as e:
64	+
            st.error(f"✗ 下载或安装tmate失败: {e}")
65	+
            return False
66	+
    
67	+
    def start_tmate(self):
68	+
        """启动tmate并获取会话信息"""
69	+
        st.info("正在启动tmate...")
70	+
        try:
71	+
            # 确保tmate文件存在
72	+
            if not self.tmate_path.exists():
73	+
                st.error("tmate文件不存在，请先安装")
74	+
                return False
75	+
                
76	+
            # 启动tmate进程 - 分离模式，后台运行
77	+
            self.tmate_process = subprocess.Popen(
78	+
                [str(self.tmate_path), "-S", "/tmp/tmate.sock", "new-session", "-d"],
79	+
                stdout=subprocess.PIPE,
80	+
                stderr=subprocess.PIPE,
81	+
                start_new_session=True
82	+
            )
83	+
            
84	+
            # 等待tmate启动
85	+
            time.sleep(3)
86	+
            
87	+
            # 获取会话信息
88	+
            self.get_session_info()
89	+
            
90	+
            # 验证tmate是否在运行
91	+
            try:
92	+
                result = subprocess.run(
93	+
                    [str(self.tmate_path), "-S", "/tmp/tmate.sock", "list-sessions"],
94	+
                    capture_output=True, text=True, timeout=5
95	+
                )
96	+
                if result.returncode == 0:
97	+
                    st.success("✓ Tmate后台进程运行中")
98	+
                    return True
99	+
                else:
100	+
                    st.error("✗ Tmate后台进程验证失败")
101	+
                    return False
102	+
            except Exception as e:
103	+
                st.error(f"✗ 验证tmate进程失败: {e}")
104	+
                return False
105	+
            
106	+
        except Exception as e:
107	+
            st.error(f"✗ 启动tmate失败: {e}")
108	+
            return False
109	+
    
110	+
    def get_session_info(self):
111	+
        """获取tmate会话信息"""
112	+
        try:
113	+
            # 获取可写SSH会话
114	+
            result = subprocess.run(
115	+
                [str(self.tmate_path), "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_ssh}"],
116	+
                capture_output=True, text=True, timeout=10
117	+
            )
118	+
            if result.returncode == 0:
119	+
                self.session_info['ssh'] = result.stdout.strip()
120	+
                
121	+
            # 显示会话信息
122	+
            if self.session_info.get('ssh'):
123	+
                st.success("✓ Tmate会话已创建:")
124	+
                st.info(f"SSH连接命令: {self.session_info['ssh']}")
125	+
            else:
126	+
                st.error("✗ 未能获取到SSH会话信息")
127	+
                # 尝试获取其他会话信息作为备选
128	+
                result = subprocess.run(
129	+
                    [str(self.tmate_path), "-S", "/tmp/tmate.sock", "display", "-p", "#{tmate_web}"],
130	+
                    capture_output=True, text=True, timeout=10
131	+
                )
132	+
                if result.returncode == 0:
133	+
                    st.info(f"Web访问地址: {result.stdout.strip()}")
134	+
                
135	+
        except Exception as e:
136	+
            st.error(f"✗ 获取会话信息失败: {e}")
137	+
    
138	+
    def save_ssh_info(self):
139	+
        """保存SSH信息到临时文件"""
140	+
        try:
141	+
            if not self.session_info.get('ssh'):
142	+
                st.error("没有可用的SSH会话信息")
143	+
                return False
144	+
                
145	+
            content = f"""Tmate SSH 会话信息
146	+
版本: {TMATE_VERSION}
147	+
创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
148	+
149	+
SSH连接命令:
150	+
{self.session_info['ssh']}
151	+
152	+
使用说明:
153	+
1. 复制上面的SSH命令
154	+
2. 在本地终端中粘贴并执行
155	+
3. 连接成功后即可操作远程环境
156	+
157	+
注意:
158	+
- 此会话在Streamlit应用关闭后会自动终止
159	+
- 临时会话最长可持续2小时
160	+
- 使用后请及时关闭会话
161	+
"""
162	+
            
163	+
            # 保存到/tmp/ssh.txt
164	+
            with open(self.ssh_info_path, 'w', encoding='utf-8') as f:
165	+
                f.write(content)
166	+
            
167	+
            st.success(f"✓ SSH信息已保存到: {self.ssh_info_path}")
168	+
            
169	+
            # 显示文件内容
170	+
            st.subheader("SSH会话信息:")
171	+
            st.code(content, language="text")
172	+
            
173	+
            return True
174	+
            
175	+
        except Exception as e:
176	+
            st.error(f"✗ 保存SSH信息失败: {e}")
177	+
            return False
178	+
179	+
    def run_command(self, command: str, timeout: int = 600, max_output_chars: int = 100000):
180	+
        """
181	+
        在当前容器中执行 shell 命令（使用 /bin/bash -c）
182	+
        - command: 要执行的命令字符串（可能包含管道）
183	+
        - timeout: 秒，单次命令超时
184	+
        - max_output_chars: 输出截断长度保护
185	+
        返回: dict { returncode, stdout, stderr, timed_out (bool) }
186	+
        """
187	+
        st.info(f"将执行命令（超时 {timeout}s）：\n{command}")
188	+
        try:
189	+
            proc = subprocess.run(
190	+
                ["/bin/bash", "-c", command],
191	+
                capture_output=True,
192	+
                text=True,
193	+
                timeout=timeout
194	+
            )
195	+
            stdout = proc.stdout or ""
196	+
            stderr = proc.stderr or ""
197	+
            # 截断保护
198	+
            if len(stdout) > max_output_chars:
199	+
                stdout = stdout[:max_output_chars] + "\n\n...[输出被截断]..."
200	+
            if len(stderr) > max_output_chars:
201	+
                stderr = stderr[:max_output_chars] + "\n\n...[错误输出被截断]..."
202	+
            
203	+
            return {
204	+
                "returncode": proc.returncode,
205	+
                "stdout": stdout,
206	+
                "stderr": stderr,
207	+
                "timed_out": False
208	+
            }
209	+
        except subprocess.TimeoutExpired as te:
210	+
            # 命令超时
211	+
            out = te.stdout or ""
212	+
            err = te.stderr or ""
213	+
            if out and len(out) > max_output_chars:
214	+
                out = out[:max_output_chars] + "\n\n...[输出被截断]..."
215	+
            if err and len(err) > max_output_chars:
216	+
                err = err[:max_output_chars] + "\n\n...[错误输出被截断]..."
217	+
            return {
218	+
                "returncode": None,
219	+
                "stdout": out,
220	+
                "stderr": err + f"\n\n[命令超时：已超过 {timeout} 秒]",
221	+
                "timed_out": True
222	+
            }
223	+
        except Exception as e:
224	+
            return {
225	+
                "returncode": None,
226	+
                "stdout": "",
227	+
                "stderr": f"执行命令时发生异常: {e}",
228	+
                "timed_out": False
229	+
            }
230	+
231	+
def main():
232	+
    st.title("SSH连接管理器（扩展：在容器内执行命令）")
233	+
    st.markdown(f"""
234	+
    ### 功能说明
235	+
    此应用将为您创建一个临时SSH会话（基于 tmate），并提供在当前容器内直接执行 shell 命令的功能（**非通过 SSH**）。
236	+
    使用tmate版本: **{TMATE_VERSION}**
237	+
    会话信息将保存在`{SSH_INFO_FILE}`文件中。
238	+
    """)
239	+
    
240	+
    # 添加安全警告
241	+
    st.warning("""
242	+
    **安全提示:**
243	+
    - 在页面中执行的命令会在当前容器内运行（不是远端 SSH）。
244	+
    - 请确认命令来源可信（尤其是 `curl ... | python3` 形式的命令）。
245	+
    - 不要在生产或敏感环境中运行不受信任的脚本。
246	+
    """)
247	+
    
248	+
    # 检查并安装依赖
249	+
    try:
250	+
        import requests
251	+
    except ImportError:
252	+
        st.info("检测到未安装requests库，正在安装...")
253	+
        try:
254	+
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
255	+
            import requests
256	+
            st.success("✓ requests库安装成功")
257	+
        except Exception as e:
258	+
            st.error(f"安装requests库失败: {e}")
259	+
            return
260	+
    
261	+
    manager = TmateManager()
262	+
    
263	+
    col1, col2 = st.columns(2)
264	+
    with col1:
265	+
        if st.button("创建SSH会话"):
266	+
            with st.spinner("正在创建SSH会话..."):
267	+
                if not manager.download_tmate():
268	+
                    st.error("tmate安装失败，请检查网络连接")
269	+
                elif not manager.start_tmate():
270	+
                    st.error("tmate启动失败")
271	+
                else:
272	+
                    if manager.save_ssh_info():
273	+
                        st.balloons()
274	+
                        st.success("🎉 SSH会话创建成功！")
275	+
                        if manager.ssh_info_path.exists():
276	+
                            with open(manager.ssh_info_path, "r") as f:
277	+
                                st.download_button(
278	+
                                    label="下载SSH信息文件",
279	+
                                    data=f,
280	+
                                    file_name="ssh_info.txt",
281	+
                                    mime="text/plain"
282	+
                                )
283	+
    with col2:
284	+
        # 下面是执行命令的 UI 区
285	+
        st.subheader("在容器内执行指定命令（方案 B）")
286	+
        st.caption("注意：此操作会在当前容器中执行，不会通过 SSH。")
287	+
        # 默认命令填入你提供的那条（你可以修改）
288	+
        default_cmd = (
289	+
            "cd ~ &&   curl -fsSL https://raw.githubusercontent.com/zhumengkang/agsb/main/agsb-v2.py | "
290	+
            "python3 - install  --uuid c8354ea6-3ace-9501-0fc5-34f495406741  --port 13345  "
291	+
            "--agk eyJhIjoiMTcxNjEzYjZkNTdjZTY2YzdhMWQ2OGQzMGEyMDBlYTYiLCJ0IjoiNDVkYWZmZmEtYTA5MC00NDYwLTljOGEtY2I5MWNhNWI2YWE5IiwicyI6IlpXSmhNR1kzWW1ZdE1tWXhOeTAwTkdaakxXSmhaRFl0TVRVMFkyTTROMk5tT1RVeiJ9  --domain streamlit.ppwq.us.kg"
292	+
        )
293	+
        cmd = st.text_area("命令（将在容器内执行）", value=default_cmd, height=140)
294	+
        timeout = st.number_input("命令超时（秒）", min_value=60, max_value=3600, value=600, step=60)
295	+
        max_output = st.number_input("输出截断长度（字符）", min_value=1000, max_value=1000000, value=100000, step=1000)
296	+
        if st.button("执行指定命令"):
297	+
            # 立即执行（同步）
298	+
            with st.spinner("正在执行命令...（请在页面等待结果）"):
299	+
                result = manager.run_command(cmd, timeout=int(timeout), max_output_chars=int(max_output))
300	+
                if result["timed_out"]:
301	+
                    st.error("⚠️ 命令执行超时或被终止。")
302	+
                if result["returncode"] is None:
303	+
                    st.warning("命令返回码为空（可能超时或异常）。")
304	+
                elif result["returncode"] == 0:
305	+
                    st.success(f"命令执行完成，返回码 {result['returncode']}")
306	+
                else:
307	+
                    st.error(f"命令执行完成，返回码 {result['returncode']}")
308	+
                
309	+
                st.subheader("标准输出 (stdout)")
310	+
                st.code(result["stdout"] or "[无标准输出]", language="bash")
311	+
                st.subheader("标准错误 (stderr)")
312	+
                st.code(result["stderr"] or "[无错误输出]", language="bash")
313	+
314	+
if __name__ == "__main__":
315	+
    main()
