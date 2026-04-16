const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

const PROTO_PATH = path.join(__dirname, '../../proto/contract.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});

const legalProto = grpc.loadPackageDefinition(packageDefinition).legal_tech;

// Note: Ensure the Python server runs on this address
const client = new legalProto.ContractAnalyzer('127.0.0.1:50051', grpc.credentials.createInsecure());

function analyzeDocument(fileBuffer, fileExtension) {
  return new Promise((resolve, reject) => {
    const request = {
      file_bytes: fileBuffer,
      file_extension: fileExtension
    };
    
    console.log(`📡 Sending document to Model (gRPC): ${fileExtension}, ${fileBuffer.length} bytes`);
    
    // Set a 5-minute deadline
    const deadline = new Date();
    deadline.setSeconds(deadline.getSeconds() + 300);

    client.AnalyzeDocument(request, { deadline }, (err, response) => {
      if (err) {
        console.error("❌ gRPC call failed:", err);
        return reject(err);
      }
      
      if (!response.success) {
        console.error("❌ Model returned error:", response.error_message);
        return reject(new Error(response.error_message || "Unknown error from model"));
      }
      
      console.log("✅ Received success response from Model (gRPC)");
      resolve(response);
    });
  });
}

module.exports = {
  analyzeDocument
};
