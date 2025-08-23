-- Sample geo data for testing the management command
-- Using simplified INSERT format for the parser

-- States
INSERT INTO states (code, name) VALUES ('UP', 'Uttar Pradesh');
INSERT INTO states (code, name) VALUES ('MP', 'Madhya Pradesh');
INSERT INTO states (code, name) VALUES ('MH', 'Maharashtra');

-- Cities  
INSERT INTO cities (state_code, name) VALUES ('UP', 'Agra');
INSERT INTO cities (state_code, name) VALUES ('UP', 'Lucknow');
INSERT INTO cities (state_code, name) VALUES ('MP', 'Bhopal');
INSERT INTO cities (state_code, name) VALUES ('MP', 'Indore');
INSERT INTO cities (state_code, name) VALUES ('MH', 'Mumbai');
INSERT INTO cities (state_code, name) VALUES ('MH', 'Pune');

-- Pincodes
INSERT INTO pincodes (state_code, city_name, code) VALUES ('UP', 'Agra', '282001');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('UP', 'Agra', '282002');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('UP', 'Lucknow', '226001');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('UP', 'Lucknow', '226002');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('MP', 'Bhopal', '462001');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('MP', 'Indore', '452001');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('MH', 'Mumbai', '400001');
INSERT INTO pincodes (state_code, city_name, code) VALUES ('MH', 'Pune', '411001');
