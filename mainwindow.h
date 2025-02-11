#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QProcess>

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    void executeScript(QString cmd);
    ~MainWindow();

private slots:
    void on_testAllBtn_clicked();

    void on_testUsbBtn_clicked();

    void on_testPciBtn_clicked();

    void on_testEmmcBtn_clicked();

    void on_testHdmiBtn_clicked();

    void on_testSataBtn_clicked();

    void on_testUartBtn_clicked();

    void on_testCanBtn_clicked();

    void on_testRs422Btn_clicked();

    void on_testEthBtn_clicked();

    void on_testRtcBtn_clicked();

    void showLogs();

    void changeProcessState(QProcess::ProcessState newState);

    void on_killProcessBtn_clicked();

    void on_testUartEndlessBtn_clicked();

private:
    QProcess* scriptProcess = new QProcess(this);
    QProcess::ProcessState processState = QProcess::NotRunning;
    Ui::MainWindow *ui;
};
#endif // MAINWINDOW_H
