import React, { useRef, useEffect, useState } from "react";
import axios from "axios";
import API_BASE_URL from "./API";

let videoRef;
let canvasRef;
let context;

function MasterComponent() {
  let [lastFrame, setLastFrame] = useState(null);
  const [showWebcam, setShowWebcam] = useState(true);
  const [showImg, setShowImg] = useState(false);

  function register_new_user_ok(text) {
    if (lastFrame) {
      const apiUrl = API_BASE_URL + "/register_new_user?text=" + text;
      console.log(typeof lastFrame);
      fetch(lastFrame)
        .then((response) => response.blob())
        .then((blob) => {
          const file = new File([blob], "webcam-frame.png", {
            type: "image/png",
          });
          const formData = new FormData();
          formData.append("file", file);

          axios
            .post(apiUrl, formData, {
              headers: {
                "Content-Type": "multipart/form-data",
              },
            })
            .then((response) => {
              console.log(response.data);
              if (response.data.registration_status == 200) {
                alert("User was registered successfully!");
              }
            })
            .catch((error) => {
              console.error("Error sending image to API:", error);
            });
        });
    }
  }

  async function downloadLogs() {
    const response = await axios.get(API_BASE_URL + "/get_attendance_logs", {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "logs.zip");
    document.body.appendChild(link);
    link.click();
  }

  function send_img_login() {
    if (videoRef.current && canvasRef.current) {
      context = canvasRef.current.getContext("2d");
      context.drawImage(videoRef.current, 0, 0, 400, 300);

      canvasRef.current.toBlob((blob) => {
        // setLastFrame(URL.createObjectURL(blob));

        // Your edition here

        const apiUrl = API_BASE_URL + "/login";
        const file = new File([blob], "webcam-frame.png", {
          type: "image/png",
        });
        const formData = new FormData();
        formData.append("file", file);

        axios
          .post(apiUrl, formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          })
          .then((response) => {
            console.log(response.data);
            if (response.data.match_status == true) {
              alert("Welcome back " + response.data.user + " !");
            } else {
              alert("Unknown user! Please try again or register new user!");
            }
          })
          .catch((error) => {
            console.error("Error sending image to API:", error);
          });
      });
    }
  }

  function send_img_logout() {
    if (videoRef.current && canvasRef.current) {
      context = canvasRef.current.getContext("2d");
      context.drawImage(videoRef.current, 0, 0, 400, 300);

      canvasRef.current.toBlob((blob) => {
        // setLastFrame(URL.createObjectURL(blob));

        // Your edition here

        const apiUrl = API_BASE_URL + "/logout";
        const file = new File([blob], "webcam-frame.png", {
          type: "image/png",
        });
        const formData = new FormData();
        formData.append("file", file);

        axios
          .post(apiUrl, formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          })
          .then((response) => {
            console.log(response.data);
            if (response.data.match_status == true) {
              alert("Goodbye " + response.data.user + " !");
            } else {
              alert("Unknown user! Please try again or register new user!");
            }
          })
          .catch((error) => {
            console.error("Error sending image to API:", error);
          });
      });
    }
  }
  return (
    <div className="master-component">
      {showWebcam ? (
        <Webcam lastFrame={lastFrame} setLastFrame={setLastFrame} />
      ) : (
        <img className="img" src={lastFrame} />
      )}
      <Buttons
        lastFrame={lastFrame}
        setLastFrame={setLastFrame}
        setShowWebcam={setShowWebcam}
        showWebcam={showWebcam}
        setShowImg={setShowImg}
        send_img_login={send_img_login}
        send_img_logout={send_img_logout}
        register_new_user_ok={register_new_user_ok}
        downloadLogs={downloadLogs}
      />
    </div>
  );
}

function saveLastFrame(
  canvasRef,
  lastFrame,
  setLastFrame,
  setShowWebcam,
  showWebcam,
  setShowImg
) {
  requestAnimationFrame(() => {
    console.log(context);

    if (!showWebcam && lastFrame) {
      setShowImg(true);
    } else {
      setShowImg(false);
    }

    if (videoRef.current && canvasRef.current) {
      context = canvasRef.current.getContext("2d");
      context.drawImage(videoRef.current, 0, 0, 400, 300);

      canvasRef.current.toBlob((blob) => {
        setLastFrame(URL.createObjectURL(blob));
        // lastFrame = blob.slice(); // Your edition here
      });
      setShowWebcam(false);
      setShowImg(true);
    }
  }, [showWebcam]);
}

function Webcam({ lastFrame, setLastFrame }) {
  videoRef = useRef(null);
  canvasRef = useRef(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [devices, setDevices] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [error, setError] = useState("");
  const [mirror, setMirror] = useState(true);

  const stopStream = () => {
    const stream = videoRef.current?.srcObject;
    if (stream && stream.getTracks) stream.getTracks().forEach(t => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
  };

  const startStream = async (deviceId = null) => {
    setError("");
    try {
      const constraints = deviceId
        ? { video: { deviceId: { exact: deviceId } }, audio: false }
        : { video: true, audio: false };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        // Wait for dimensions so canvas matches
        await videoRef.current.play().catch(()=>{});
        setIsStreaming(true);
      }
    } catch (e) {
      setError(e.message || "Unable to access camera");
      setIsStreaming(false);
    }
  };

  const refreshDevices = async () => {
    const all = await navigator.mediaDevices.enumerateDevices();
    const cams = all.filter(d => d.kind === "videoinput")
                   .map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Camera ${i+1}` }));
    setDevices(cams);
    if (!selectedId && cams.length) setSelectedId(cams[0].deviceId);
  };

  // First-time permission (so labels appear), then list devices
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const temp = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        temp.getTracks().forEach(t => t.stop());
        if (!cancelled) await refreshDevices();
      } catch {
        setError("Camera permission denied or unavailable.");
      }
    })();

    const onChange = () => refreshDevices();
    navigator.mediaDevices?.addEventListener?.("devicechange", onChange);
    return () => {
      cancelled = true;
      navigator.mediaDevices?.removeEventListener?.("devicechange", onChange);
      stopStream();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Start whenever a selection is made
  useEffect(() => {
    if (!selectedId) return;
    stopStream();
    startStream(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  // Keep lastFrame updated
  useEffect(() => {
    if (!isStreaming || !videoRef.current || !canvasRef.current) return;

    const v = videoRef.current;
    const c = canvasRef.current;
    const ctx = c.getContext("2d");

    const resize = () => {
      const w = v.videoWidth || 640;
      const h = v.videoHeight || 480;
      c.width = 400;              // your fixed capture size
      c.height = 300;
    };
    resize();

    let raf;
    const tick = () => {
      // draw from video → canvas
      // mirror if needed
      const w = c.width, h = c.height;
      ctx.save();
      ctx.clearRect(0, 0, w, h);
      if (mirror) {
        ctx.translate(w, 0);
        ctx.scale(-1, 1);
      }
      ctx.drawImage(v, 0, 0, w, h);
      ctx.restore();

      c.toBlob((blob) => {
        if (blob) setLastFrame(URL.createObjectURL(blob));
      }, "image/png");

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(raf);
  }, [isStreaming, mirror, setLastFrame]);

  return (
    <div className="webcam" style={{ display: "grid", gap: 8 }}>
      {/* controls */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <label htmlFor="cameraSelect" style={{ fontSize: 14 }}>Camera:</label>
        <select
          id="cameraSelect"
          value={selectedId}
          onChange={(e) => setSelectedId(e.target.value)}
          style={{ padding: "4px 8px" }}
        >
          {devices.map(d => (
            <option key={d.deviceId} value={d.deviceId}>{d.label}</option>
          ))}
          {devices.length === 0 && <option>No cameras found</option>}
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
          <input type="checkbox" checked={mirror} onChange={e => setMirror(e.target.checked)} />
          Mirror
        </label>
        {!isStreaming && <span style={{ fontSize: 12, color: "#a60" }}>not streaming</span>}
      </div>

      {/* preview + capture canvas (overlay) */}
      <div style={{ position: "relative", width: 400, height: 300 }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{
            width: 400,
            height: 300,
            objectFit: "cover",
            transform: mirror ? "scaleX(-1)" : "none",
            borderRadius: 8,
            background: "#000"
          }}
        />
        {/* keep canvas invisible if you don't want to show it; it's for capture */}
        <canvas
          ref={canvasRef}
          width={400}
          height={300}
          style={{ position: "absolute", inset: 0, opacity: 0, pointerEvents: "none" }}
        />
      </div>

      {error && <p style={{ color: "#a00", fontSize: 12 }}>{error}</p>}
    </div>
  );
}

function Buttons({
  lastFrame,
  setLastFrame,
  setShowWebcam,
  showWebcam,
  setShowImg,
  send_img_login,
  send_img_logout,
  register_new_user_ok,
  downloadLogs,
}) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const [zIndexAdmin, setZIndexAdmin] = useState(1);
  const [zIndexRegistering, setZIndexRegistering] = useState(1);

  const changeZIndexAdmin = (newZIndex) => {
    setZIndexAdmin(newZIndex);
  };

  const changeZIndexRegistering = (newZIndex) => {
    setZIndexRegistering(newZIndex);
  };

  const [value, setValue] = useState("");

  const handleChange = (event) => {
    setValue(event.target.value);
  };

  const resetTextBox = () => {
    setValue("");
  };

  return (
    <div className="buttons-container">
      <div
        className={`${
          isRegistering ? "visible" : "hidden"
        } register-text-container`}
        style={{
          zIndex: zIndexRegistering,
        }}
      >
        <input
          className="register-text"
          type="text"
          placeholder="Enter user name"
          value={value}
          onChange={handleChange}
        />
      </div>
      <div
        className="register-ok-container"
        style={{
          zIndex: zIndexRegistering,
        }}
      >
        <button
          className={`${
            isRegistering ? "visible" : "hidden"
          } register-ok-button`}
          onClick={async () => {
            setIsAdmin(false);
            setIsRegistering(false);

            changeZIndexAdmin(1);
            changeZIndexRegistering(1);

            setShowWebcam(true);
            setShowImg(false);
            register_new_user_ok(value);
          }}
        ></button>
      </div>
      <div
        className="register-cancel-container"
        style={{
          zIndex: zIndexRegistering,
        }}
      >
        <button
          className={`${
            isRegistering ? "visible" : "hidden"
          } register-cancel-button`}
          onClick={async () => {
            setIsAdmin(false);
            setIsRegistering(false);

            changeZIndexAdmin(1);
            changeZIndexRegistering(1);

            setShowWebcam(true);
            setShowImg(false);
          }}
        ></button>
      </div>
      <div className="login-container">
        <button
          className={`${
            isAdmin || isRegistering ? "hidden" : "visible"
          } login-button`}
          onClick={async () => {
            // saveFrameToDisk(canvasRef, lastFrame, setLastFrame);
            // setIsRegistering(true);
            send_img_login();
          }}
        ></button>
      </div>
      <div className="logout-container">
        <button
          className={`${
            isAdmin || isRegistering ? "hidden" : "visible"
          } logout-button`}
          onClick={() => {
            send_img_logout();
          }}
        ></button>
      </div>
      <div className="admin-container">
        <button
          className={`${
            isAdmin || isRegistering ? "hidden" : "visible"
          } admin-button`}
          onClick={() => {
            setIsAdmin(true);
            setIsRegistering(false);

            changeZIndexAdmin(3);
            changeZIndexRegistering(1);
          }}
        ></button>
      </div>
      <div
        className="register-container"
        style={{
          zIndex: zIndexAdmin,
        }}
      >
        <button
          className={`${isAdmin ? "visible" : "hidden"} register-button`}
          onClick={() => {
            setIsAdmin(false);
            setIsRegistering(true);

            changeZIndexAdmin(1);
            changeZIndexRegistering(3);

            saveLastFrame(
              canvasRef,
              lastFrame,
              setLastFrame,
              setShowWebcam,
              showWebcam,
              setShowImg
            );
            resetTextBox();

          }}
        ></button>
      </div>
      <div
        className="goback-container"
        style={{
          zIndex: zIndexAdmin,
        }}
      >
        <button
          className={`${isAdmin ? "visible" : "hidden"} goback-button`}
          onClick={() => {
            setIsAdmin(false);
            setIsRegistering(false);

            changeZIndexAdmin(1);
            changeZIndexRegistering(1);
          }}
        ></button>
      </div>

      <div
        className="download-container"
        style={{
          zIndex: zIndexAdmin,
        }}
      >
        <button
          className={`${isAdmin ? "visible" : "hidden"} download-button`}
          onClick={() => {
            setIsAdmin(false);
            setIsRegistering(false);

            changeZIndexAdmin(1);
            changeZIndexRegistering(1);

            downloadLogs();
          }}
        ></button>
      </div>
    </div>
  );
}
export default MasterComponent;
