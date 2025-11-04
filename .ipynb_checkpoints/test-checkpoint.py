import mediapipe as mp, cv2

mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils
face_mesh = mp_face.FaceMesh(static_image_mode=True)

image = cv2.imread("1.jpg")
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
res = face_mesh.process(rgb)

if res.multi_face_landmarks:
    for lm in res.multi_face_landmarks:
        mp_draw.draw_landmarks(
            image, lm, mp_face.FACEMESH_TESSELATION,
            mp_draw.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1)
        )

cv2.imwrite("face_landmarks_debug.jpg", image)
