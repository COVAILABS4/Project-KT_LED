import React, { useState } from "react";
import { Modal, Button, Container, Row, Col } from "react-bootstrap";

const colors = [
  [255, 0, 0], // Red
  [0, 255, 0], // Green
  [0, 0, 255], // Blue
  [255, 255, 0], // Yellow
  [0, 255, 255], // Cyan
  [255, 0, 255], // Magenta
  [255, 165, 0], // Orange
  [128, 0, 128], // Purple
  [165, 42, 42], // BROWN
  [0, 255, 123], // Lime
];

const ColorPickerModal = ({
  show,
  handleClose,
  handleColorUpdate,
  setNewColor,
}) => {
  const [selectedColor, setSelectedColor] = useState(null);

  const handleColorClick = (color) => {
    setSelectedColor(color);
    setNewColor(color);
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Select a Color</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Container>
          <Row>
            {colors.map((color, index) => (
              <Col key={index} xs={4} className="mb-2">
                <div
                  style={{
                    backgroundColor: `rgb(${color.join(",")})`,
                    width: "50px",
                    height: "50px",
                    cursor: "pointer",
                    border:
                      selectedColor === color ? "3px solid black" : "none",
                  }}
                  onClick={() => handleColorClick(color)}
                />
              </Col>
            ))}
          </Row>
        </Container>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose}>
          Cancel
        </Button>
        <Button variant="primary" onClick={handleColorUpdate}>
          Update
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ColorPickerModal;
