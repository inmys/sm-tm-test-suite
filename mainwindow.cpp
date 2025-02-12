#include "mainwindow.h"
#include "./ui_mainwindow.h"
#include <QProcess>
#include <QThread>
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    setWindowTitle("Periphery tester");
    connect(scriptProcess, &QProcess::readyReadStandardOutput, this, &MainWindow::showLogs);
    connect(scriptProcess, &QProcess::stateChanged, this, &MainWindow::changeProcessState);
}
MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::executeScript(QString cmd){
    if (processState == QProcess::NotRunning){
        QStringList params;
        //params << "-u" <<"/home/garlicdogg/projects/3_rk3568_telematika_smtm/burn/python-test-suite/test-sm-tm.py" << "-q";
        params << "-u" <<"/root/test-sm-tm.py" << "-q";
        if (ui->isDebugMode->isChecked()){
            params << "-v";
        }
        params << cmd;
        QString program = "python3";
        scriptProcess->start(program, params);
    }
}
void MainWindow::on_testAllBtn_clicked()
{
    executeScript("COMPLEX");
}
void MainWindow::on_testUsbBtn_clicked()
{
    executeScript("USB");
}
void MainWindow::on_testPciBtn_clicked()
{
    executeScript("PCI");
}
void MainWindow::on_testHdmiBtn_clicked()
{
    executeScript("HDMI");
}
void MainWindow::on_testUartBtn_clicked()
{
    executeScript("UART");
}
void MainWindow::on_testUartEndlessBtn_clicked()
{
    executeScript("UART_ENDLESS");
}
void MainWindow::on_testRs422Btn_clicked()
{
    executeScript("RS422");
}
void MainWindow::on_testSataBtn_clicked()
{
    executeScript("SATA");
}
void MainWindow::on_testRtcBtn_clicked()
{
    executeScript("RTC");
}
void MainWindow::on_testCanBtn_clicked()
{
    executeScript("CAN");
}
void MainWindow::on_testEmmcBtn_clicked()
{
    executeScript("EMMC");
}
void MainWindow::on_testEthBtn_clicked()
{
    executeScript("ETHERNET");
}
void MainWindow::showLogs()
{
    QString data = scriptProcess->readAllStandardOutput();
    QString firstWord, record;
    QStringList dataList = data.split("\n");
    for (int i = 0; i<dataList.length()-1; i++){
        record = dataList.at(i);
        QStringList wordsList = record.split(" ");
        firstWord = wordsList.at(0);
        if (firstWord == "[ERROR]"){
            ui->logText->append("<font color='#ff3333'>" + record + "</font>");
        } else if (firstWord == "[OK]"){
            ui->logText->append("<font color='#52bf82'>" + record + "</font>");
        } else if (firstWord == "[FAIL]"){
            ui->logText->append("<b><font color='#cc0000'>" + record + "</font></b>");
        } else if (firstWord == "[SUCCESS]"){
            ui->logText->append("<b><font color='#43a23c'>" + record + "</font></b>");
        } else if (firstWord == "[START]"){
            ui->logText->append("<b>" + record + "</b>");

        } else{
            ui->logText->append(record);
        }
    }


}

void MainWindow::changeProcessState(QProcess::ProcessState newState)
{
    processState = newState;
    if(newState == QProcess::NotRunning){
        ui->processState->setText("Состояние процесса: Выключен");
    } else if(newState == QProcess::Starting){
        ui->processState->setText("Состояние процесса: Запускается");
    } else if(newState == QProcess::Running){
        ui->processState->setText("Состояние процесса: В работе");
    } else{
        ui->processState->setText("Состояние процесса: Неизвестно");
    }

}

void MainWindow::on_killProcessBtn_clicked()
{
    scriptProcess->kill();
}



