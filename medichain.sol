// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract HospitalSystem is Ownable {

    constructor(address _initialOwner) Ownable(_initialOwner) {}

    // ===================== Structs =====================

    struct Doctor {
        string name;
        string specialization;
        bool isVerified;
    }

    struct Patient {
        string name;
        address backupWallet;
        bool exists;
    }

    struct MedicalRecord {
        uint256 recordId;
        address doctorId;
        address patientId;
        uint256 timestamp;
        string recordType;
        string ipfsHash;     // Stores encrypted IPFS file hash
        string notes;
        uint8 version;
        bool isEncrypted;    // NEW: Indicates if IPFS file is encrypted
    }

    // ===================== State Variables =====================

    uint256 public recordCounter;

    mapping(address => Doctor) public doctors;
    mapping(address => Patient) public patients;
    mapping(address => mapping(address => bool)) public patientToDoctorAccess;
    mapping(address => mapping(address => bool)) public emergencyAccess;

    mapping(address => MedicalRecord[]) public recordsByPatient;
    mapping(address => uint8[]) public doctorRatings;
    mapping(address => mapping(string => uint8)) public recordVersionByType;

    // ===================== Events =====================

    event DoctorAdded(address indexed doctor);
    event DoctorVerified(address indexed doctor);
    event PatientRegistered(address indexed patient);
    event RecordAdded(address indexed patient, address indexed doctor, uint256 recordId);

    // ===================== Modifiers =====================

    modifier onlyVerifiedDoctor() {
        require(doctors[msg.sender].isVerified, "Not a verified doctor");
        _;
    }

    modifier onlyExistingPatient(address patientAddr) {
        require(patients[patientAddr].exists, "Patient not registered");
        _;
    }

    // ===================== Admin Functions =====================

    function addDoctor(
        address _doctorAddr,
        string memory _name,
        string memory _specialization
    ) public onlyOwner {
        doctors[_doctorAddr] = Doctor(_name, _specialization, false);
        emit DoctorAdded(_doctorAddr);
    }

    function verifyDoctor(address _doctorAddr) public onlyOwner {
        require(bytes(doctors[_doctorAddr].name).length > 0, "Doctor not added");
        doctors[_doctorAddr].isVerified = true;
        emit DoctorVerified(_doctorAddr);
    }

    // ===================== Patient Functions =====================

    function registerPatient(string memory _name, address _backupWallet) public {
        require(!patients[msg.sender].exists, "Already registered");
        patients[msg.sender] = Patient(_name, _backupWallet, true);
        emit PatientRegistered(msg.sender);
    }

    function grantAccessToDoctor(address _doctorAddr) public {
        require(doctors[_doctorAddr].isVerified, "Doctor not verified");
        patientToDoctorAccess[msg.sender][_doctorAddr] = true;
    }

    function revokeAccessFromDoctor(address _doctorAddr) public {
        patientToDoctorAccess[msg.sender][_doctorAddr] = false;
    }

    // ===================== Emergency Access =====================

    function grantEmergencyAccess(address _patientAddr, address _doctorAddr) public {
        require(
            msg.sender == owner() || msg.sender == patients[_patientAddr].backupWallet,
            "Only owner or backup wallet can grant emergency access"
        );
        require(doctors[_doctorAddr].isVerified, "Doctor not verified");
        require(patients[_patientAddr].exists, "Patient not found");

        emergencyAccess[_patientAddr][_doctorAddr] = true;
    }

    function hasEmergencyAccess(address _patientAddr, address _doctorAddr) public view returns (bool) {
        return emergencyAccess[_patientAddr][_doctorAddr];
    }

    // ===================== Rating System =====================

    function rateDoctor(address _doctorAddr, uint8 _rating) public {
        require(patients[msg.sender].exists, "Only registered patients can rate");
        require(doctors[_doctorAddr].isVerified, "Doctor must be verified");
        require(_rating >= 1 && _rating <= 5, "Rating must be between 1 and 5");

        doctorRatings[_doctorAddr].push(_rating);
    }

    function getAverageRating(address _doctorAddr) public view returns (uint256) {
        uint8[] memory ratings = doctorRatings[_doctorAddr];
        if (ratings.length == 0) return 0;

        uint256 sum = 0;
        for (uint256 i = 0; i < ratings.length; i++) {
            sum += ratings[i];
        }

        return sum / ratings.length;
    }

    // ===================== Medical Record Management =====================

    function addMedicalRecord(
        address _patientAddr,
        string memory _recordType,
        string memory _ipfsHash,
        string memory _notes,
        bool _isEncrypted // NEW: is IPFS file encrypted?
    ) public onlyVerifiedDoctor onlyExistingPatient(_patientAddr) {
        require(
            patientToDoctorAccess[_patientAddr][msg.sender] || emergencyAccess[_patientAddr][msg.sender],
            "Access not granted"
        );

        recordCounter++;
        uint8 version = ++recordVersionByType[_patientAddr][_recordType];

        MedicalRecord memory newRecord = MedicalRecord(
            recordCounter,
            msg.sender,
            _patientAddr,
            block.timestamp,
            _recordType,
            _ipfsHash,
            _notes,
            version,
            _isEncrypted
        );

        recordsByPatient[_patientAddr].push(newRecord);
        emit RecordAdded(_patientAddr, msg.sender, recordCounter);
    }

    function getPatientRecords(address _patientAddr) public view returns (MedicalRecord[] memory) {
        require(
            msg.sender == _patientAddr || 
            patientToDoctorAccess[_patientAddr][msg.sender] || 
            emergencyAccess[_patientAddr][msg.sender],
            "Access denied"
        );
        return recordsByPatient[_patientAddr];
    }

    function getRecordById(address _patientAddr, uint256 _recordId) public view returns (MedicalRecord memory) {
        require(
            msg.sender == _patientAddr || 
            patientToDoctorAccess[_patientAddr][msg.sender] || 
            emergencyAccess[_patientAddr][msg.sender],
            "Access denied"
        );

        MedicalRecord[] memory records = recordsByPatient[_patientAddr];
        for (uint256 i = 0; i < records.length; i++) {
            if (records[i].recordId == _recordId) {
                return records[i];
            }
        }

        revert("Record not found");
    }

    function getRecordsByType(address _patientAddr, string memory _recordType) public view returns (MedicalRecord[] memory) {
        require(
            msg.sender == _patientAddr || 
            patientToDoctorAccess[_patientAddr][msg.sender] || 
            emergencyAccess[_patientAddr][msg.sender],
            "Access denied"
        );

        MedicalRecord[] memory allRecords = recordsByPatient[_patientAddr];
        uint256 count = 0;

        for (uint256 i = 0; i < allRecords.length; i++) {
            if (keccak256(bytes(allRecords[i].recordType)) == keccak256(bytes(_recordType))) {
                count++;
            }
        }

        MedicalRecord[] memory filtered = new MedicalRecord[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < allRecords.length; i++) {
            if (keccak256(bytes(allRecords[i].recordType)) == keccak256(bytes(_recordType))) {
                filtered[index++] = allRecords[i];
            }
        }

        return filtered;
    }

    function getRecordsByDoctor(address _patientAddr, address _doctorAddr) public view returns (MedicalRecord[] memory) {
        require(
            msg.sender == _patientAddr || 
            patientToDoctorAccess[_patientAddr][msg.sender] || 
            emergencyAccess[_patientAddr][msg.sender],
            "Access denied"
        );

        MedicalRecord[] memory allRecords = recordsByPatient[_patientAddr];
        uint256 count = 0;

        for (uint256 i = 0; i < allRecords.length; i++) {
            if (allRecords[i].doctorId == _doctorAddr) {
                count++;
            }
        }

        MedicalRecord[] memory filtered = new MedicalRecord[](count);
        uint256 index = 0;

        for (uint256 i = 0; i < allRecords.length; i++) {
            if (allRecords[i].doctorId == _doctorAddr) {
                filtered[index++] = allRecords[i];
            }
        }

        return filtered;
    }
}
