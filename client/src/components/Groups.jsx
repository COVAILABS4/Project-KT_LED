import React from "react";
import "./Groups.css";

const Groups = ({ data, handleBinClick }) => {
  return (
    <div className="groups-section">
      {data.length !== 0 ? (
        <h2 className="groups-header">Station</h2>
      ) : (
        <h2 className="groups-header">No Stations Found</h2>
      )}
      {data.map((group, index) => (
        <div key={index} className="group-container">
          <h3>{group.Group_id}</h3>
          <div className="group-tables">
            {group.racks.map((rack) => (
              <table
                className="single-column-table"
                key={rack.rack_id}
                style={{}}
              >
                <thead>
                  <tr>
                    <th>{rack.rack_id}</th>
                  </tr>
                </thead>
                <tbody>
                  {rack.bins.map((bin, rowIndex) => {
                    // Normalize bin color to ensure it's in the correct format
                    const colorArray = Array.isArray(bin.color)
                      ? bin.color
                      : bin.color.split(",").map(Number);

                    return (
                      <tr key={rowIndex}>
                        <td
                          style={{
                            backgroundColor: bin.clicked
                              ? "gray"
                              : `rgb(${bin.color})`,
                          }}
                          onClick={() => {
                            handleBinClick(
                              group.Group_id,
                              rack.rack_id,
                              bin.bin_id
                            );
                          }}
                        >
                          <p style={{ margin: "0px", padding: "0" }}>
                            {bin.bin_id}
                          </p>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Groups;
