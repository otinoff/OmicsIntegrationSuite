#!/usr/bin/env python3
"""
БЕЗОПАСНЫЙ деплой на production
НЕ трогает Nginx конфигурацию!
"""
import paramiko
import sys

HOST = "5.35.88.251"
USER = "root"
PASSWORD = "pA48cQu9Z2xS"
REMOTE_PATH = "/var/OmicsIntegrationSuite"

def run_ssh_command(ssh, command):
    """Run command and return output"""
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

def safe_deploy():
    """Безопасное обновление БЕЗ изменения Nginx"""
    print(f"🚀 Connecting to {HOST}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        print("✅ Connected!")
        print("="*60)

        # 1. Pull latest code
        print("\n1️⃣ Pulling latest code from GitHub...")
        out, err = run_ssh_command(ssh, f"cd {REMOTE_PATH} && git pull origin main")
        print(out)
        if "Already up to date" in out:
            print("✅ Code is up to date")
        elif "Fast-forward" in out or "Updating" in out:
            print("✅ Code updated successfully")
        else:
            print(f"⚠️ Unexpected output: {out}")

        # 2. Check if Streamlit is running
        print("\n2️⃣ Checking current Streamlit status...")
        out, err = run_ssh_command(ssh, "ps aux | grep 'streamlit.*OmicsIntegrationSuite' | grep -v grep")

        if out:
            print("✅ Streamlit is currently running")
            print(out)

            # Kill only OmicsIntegrationSuite process
            print("\n3️⃣ Stopping OmicsIntegrationSuite Streamlit...")
            run_ssh_command(ssh, "pkill -f 'streamlit.*web_interface'")
            print("✅ Stopped")

            import time
            time.sleep(2)
        else:
            print("⚠️ Streamlit not running (will start fresh)")

        # 3. Start Streamlit (SAFE - не трогает Nginx!)
        print("\n4️⃣ Starting Streamlit...")
        out, err = run_ssh_command(ssh, f"cd {REMOTE_PATH} && bash start_streamlit.sh 2>&1")
        print(out)

        # Wait for startup
        import time
        time.sleep(5)

        # 4. Verify
        print("\n5️⃣ Verifying deployment...")
        out, err = run_ssh_command(ssh, "ps aux | grep streamlit | grep web_interface | grep -v grep")

        if out:
            print("✅ Streamlit is running!")
            print(out)
        else:
            print("❌ Streamlit NOT running!")
            print("\n📋 Checking logs...")
            out, err = run_ssh_command(ssh, f"cd {REMOTE_PATH} && tail -20 streamlit.log")
            print(out)
            return 1

        # 5. Check port
        print("\n6️⃣ Checking port 8520...")
        out, err = run_ssh_command(ssh, "ss -tulpn | grep 8520")
        if out:
            print("✅ Port 8520 is listening")
            print(out)
        else:
            print("❌ Port 8520 NOT listening!")
            return 1

        # 6. Test HTTP
        print("\n7️⃣ Testing HTTP response...")
        out, err = run_ssh_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8520")
        http_code = out.strip()
        if http_code == "200":
            print(f"✅ HTTP {http_code} - SUCCESS!")
        else:
            print(f"❌ HTTP {http_code} - FAILED!")
            return 1

        # 7. Show recent commits
        print("\n8️⃣ Deployed version:")
        out, err = run_ssh_command(ssh, f"cd {REMOTE_PATH} && git log --oneline -3")
        print(out)

        print("\n" + "="*60)
        print("✅ SAFE DEPLOYMENT COMPLETE!")
        print("="*60)
        print("\n🌐 Test: https://omicsintegrationsuite.onff.ru/")
        print("\n📋 Key points:")
        print("  • Code updated from GitHub")
        print("  • Streamlit restarted")
        print("  • Nginx configuration UNCHANGED (safe!)")
        print("  • Port 8520 responding")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        ssh.close()

if __name__ == '__main__':
    sys.exit(safe_deploy())
