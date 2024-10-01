# JETSSH

JETSSH is a user-friendly SSH client built with PyQt and Paramiko, designed for Linux and macOS environments. It offers real-time terminal-like interaction, SCP/SFTP file transfer, and an intuitive GUI. Whether you need to manage servers or transfer files securely, JETSSH provides a seamless experience.

## Features

- **SSH Client with Real-Time Terminal**: Execute Linux commands and use utilities in real-time, with terminal-like output.
- **Current Working Directory**: Easily track and display the current working directory while connected via SSH.
- **File Transfer (SCP/SFTP)**: Securely upload or download files using a graphical file browser, integrated into the SSH client.
- **Cross-Platform**: Supports both macOS and Linux.
- **RPM Packaging**: Ready to be packaged as an installable RPM program.

## Installation

To install JETSSH, follow these steps:

### Prerequisites
- Python 3.7+
- PyQt5
- Paramiko
- SCP
- SFTP

### Steps

1. Clone this repository:
    ```bash
    git clone https://github.com/mmckinn6/JETSSH.git
    ```

2. Navigate into the project directory:
    ```bash
    cd JETSSH
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:
    ```bash
    python main.py
    ```

### Optional: Packaging into an RPM

To package the application into an RPM for installation on Linux systems, follow these steps:

1. Ensure that `rpm-build` is installed on your system.
2. Build the RPM package using the following command:
    ```bash
    python setup.py bdist_rpm
    ```
    
## Usage

### SSH Client
- Launch the application and click on the "Launch Session" button to connect to an SSH server.
- Execute commands directly in the terminal window. The current working directory will be displayed and updated dynamically.

### File Transfer (SCP/SFTP)
- Use the file browser to select files for transfer. You can upload or download files to and from the remote server.

## Roadmap

- [ ] Add predefined commands feature.
- [ ] Support for Windows.
- [ ] Improve UI/UX for a more intuitive experience.
- [ ] Extend file transfer functionality
- [ ] Add more customizable themes
- [ ] Add SSH Key Generation features
- [ ] Improve compatibility with text editor utilities such as vim




## Contributing

Contributions are welcome! If you'd like to contribute to JETSSH, feel free to open an issue or submit a pull request.

1. Fork the repository.
2. Create your feature branch: 
    ```bash
    git checkout -b feature-branch
    ```
3. Commit your changes: 
    ```bash
    git commit -m 'Add some feature'
    ```
4. Push to the branch: 
    ```bash
    git push origin feature-branch
    ```
5. Submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions, suggestions, or issues, please reach out at: [mmckinn6](https://github.com/mmckinn6) or (nwylds)(https://github.com/nwylds) 
