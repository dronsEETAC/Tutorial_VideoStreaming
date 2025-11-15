
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml.Linq;


namespace Receptor
{
  
    public partial class Form1 : Form
    {
        TcpListener listener;
        Process pythonProcess;
        public Form1()
        {
            InitializeComponent();
        }
        private async void button1_Click(object sender, EventArgs e)
        {
            await StartPythonAndServerAsync();
        }

        private async Task StartPythonAndServerAsync()
        {
            // --- Iniciar servidor TCP ---
            listener = new TcpListener(IPAddress.Loopback, 5000);
            listener.Start();

            // --- Lanzar Python ---
            pythonProcess = new Process();
            pythonProcess.StartInfo.FileName = @"C:\Users\Miguel\Documents\Miguel\DEE\videoStreaming\.venv\Scripts\python.exe";
            pythonProcess.StartInfo.Arguments = @"C:\Users\Miguel\Documents\Miguel\DEE\videoStreaming\Extras\ReceptorWebRTCGlobalCs\receiverParaCs.py";

            pythonProcess.StartInfo.UseShellExecute = false;
            pythonProcess.Start();

            // --- Aceptar conexión del script Python ---
            var client = await listener.AcceptTcpClientAsync();
            var stream = client.GetStream();
            Console.WriteLine("Empezamos");

            // --- Leer frames ---
            await Task.Run(() =>
            {
                while (true)
                {
                    try
                    {
                        // Leer tamaño (4 bytes)
                        byte[] lengthBytes = new byte[4];
                        int read = stream.Read(lengthBytes, 0, 4);
                        if (read == 0) break;
                        Console.WriteLine("Recibo frame");

                        int length = IPAddress.NetworkToHostOrder(BitConverter.ToInt32(lengthBytes, 0));

                        // Leer los datos JPEG
                        byte[] buffer = new byte[length];
                        int offset = 0;

                        while (offset < length)
                        {
                            int r = stream.Read(buffer, offset, length - offset);
                            if (r == 0) break;
                            offset += r;
                        }

                        // Convertir a Bitmap
                        using (var ms = new MemoryStream(buffer))
                        {
                            Image img = Image.FromStream(ms);

                            // Mostrar en el PictureBox
                            pictureBox1.Invoke(new Action(() =>
                            {
                                pictureBox1.Image?.Dispose();
                                pictureBox1.Image = new Bitmap(img);
                            }));
                        }
                    }
                    catch
                    {
                        break;
                    }
                }
            });
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }
    }
}


