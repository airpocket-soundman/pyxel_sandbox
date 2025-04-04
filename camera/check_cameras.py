import cv2

def list_cameras(max_devices=10):
    print("📷 接続されているカメラをスキャン中...")
    for i in range(max_devices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Windows なら CAP_DSHOW 推奨
        if cap is not None and cap.isOpened():
            print(f"✅ カメラデバイス {i} が使用可能です")
            cap.release()
        else:
            print(f"❌ カメラデバイス {i} は使用できません")

list_cameras()
