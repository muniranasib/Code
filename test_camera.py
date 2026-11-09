import cv2

def test_cameras():
    for index in range(6):
        camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if not camera.isOpened():
            camera.release()
            continue

        success, frame = camera.read()

        if success:
            print(f"Kamera {index} fungerer!")

            cv2.imshow(f"Camera {index}", frame)

            print("Trykk Y hvis dette er riktig kamera.")
            print("Trykk N hvis dette er feil kamera.")

            key = cv2.waitKey(0) & 0xFF

            if key == ord("y"):
                print(f"\nRiktig kameraindeks er: {index}")
                camera.release()
                cv2.destroyAllWindows()
                return index

        camera.release()
        cv2.destroyAllWindows()

    print("Fant ikke riktig kamera.")
    return None


if __name__ == "__main__":
    test_cameras()