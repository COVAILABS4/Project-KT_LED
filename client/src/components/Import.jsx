import React, { useState } from "react";
import axios from "axios";
import {
  Form,
  Button,
  Container,
  Row,
  Col,
  Alert,
  Spinner,
} from "react-bootstrap";
import Spreadsheet from "react-spreadsheet";
import * as XLSX from "xlsx";

const Import = ({ fetchData }) => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [excelData, setExcelData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    e.preventDefault();
    const files = e.target.files[0];
    setFile(files);

    if (files) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const data = e.target.result;
        const workbook = XLSX.read(data, { type: "array" });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        const dataForSpreadsheet = json.map((row) =>
          row.map((cell) => ({ value: cell }))
        );
        setExcelData(dataForSpreadsheet);
      };
      reader.readAsArrayBuffer(files);
    }
  };

  const handleFileUpload = (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);
    const ip = window.location.hostname;

    axios
      .post("http://" + ip + ":5000/import", formData)
      .then((response) => {
        setMessage("File uploaded successfully");
        fetchData();
        setExcelData(null);
        setFile(null);
        setLoading(false);
      })
      .catch((error) => {
        setMessage("File upload failed");
        console.error("There was an error uploading the file!", error);
        setLoading(false);
      });
  };

  const handleDownloadSample = () => {
    const ip = window.location.hostname;
    window.open(`http://${ip}:5000/download-sample`, "_blank");
  };

  return (
    <Container className="mt-5">
      <Row className="justify-content-md-center">
        <Col md={8}>
          <h2 className="text-center">Import Schedule</h2>
          {message && <Alert variant="info">{message}</Alert>}
          {loading ? (
            <div className="text-center">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading...</span>
              </Spinner>
              <p>Please wait, processing file...</p>
            </div>
          ) : (
            <>
              <Form onSubmit={handleFileUpload} encType="multipart/form-data">
                <Form.Group controlId="formFile" className="mb-3">
                  <Form.Label>Upload .xlsx file</Form.Label>
                  <Form.Control type="file" onChange={handleFileChange} />
                </Form.Group>
                <Button variant="primary" type="submit" className="w-100">
                  Upload
                </Button>
              </Form>
              {excelData && (
                <div style={{ alignItems: "center" }} className="mt-3">
                  <h4 className="text-center">Uploaded Data</h4>
                  <Spreadsheet data={excelData} onChange={setExcelData} />
                </div>
              )}
              <Button
                variant="secondary"
                onClick={handleDownloadSample}
                className="mt-3 w-100"
              >
                Download Sample Format
              </Button>
            </>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default Import;
