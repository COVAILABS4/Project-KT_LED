import React from "react";
import { Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

const Header = ({ data }) => {
  const navigate = useNavigate();

  const downloadJSON = (data) => {
    const fileName = "data.json";
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <div className="header">
      <h1>Dashboard</h1>
      <div
        style={{
          display: "flex",
          justifyContent: "space-evenly",
          width: "50%",
        }}
      >
        <Button href="/setup" variant="info" className="button-styled">
          Setup
        </Button>
        {/* <Button
          variant="success"
          onClick={() => downloadJSON(data)}
          className="button-styled"
        >
          Download
        </Button> */}
        <Button
          variant="primary"
          onClick={() => navigate("/import")}
          className="button-styled"
        >
          Import
        </Button>
        <Button
          variant="danger"
          onClick={handleLogout}
          className="button-styled"
        >
          Logout
        </Button>
      </div>
    </div>
  );
};

export default Header;
