import os
import zipfile
import shutil

if __name__=="__main__":
    path_folder=[]
    txt_file_name = 'archiv_list.txt'
    zip_file_name = 'archive.zip'

    with open(txt_file_name, 'r') as f:
        path_folder=f.readlines()

    if os.path.isfile(os.path.join(os.getcwd(),zip_file_name)):
        os.remove(os.path.join(os.getcwd(),zip_file_name))

    zip_ = zipfile.ZipFile(f'{os.path.join(os.getcwd(),zip_file_name)}', 'a')
    for file_ in path_folder:
        try:
            file_ = file_.strip()
            if os.path.isdir(os.path.join(os.getcwd(),file_)):
                for dirname, subdirs, files in os.walk(file_):
                    zip_.write(dirname)
                    for filename in files:
                        zip_.write(os.path.join(dirname, filename))
            else:
                zip_.write(file_)
        except:
            pass
    zip_.close()
    print("Complete!")


    # for file_ in path_folder:
    #     try:
    #         file_=file_.strip()
    #         shutil.make_archive(f'{os.path.join(os.getcwd(),os.path.splitext(os.path.basename(zip_file_name))[0])}',
    #                             'zip', os.path.join(os.getcwd(), file_)
    #                             ,base_dir='cc')
    #         # zip_.write(os.path.join(os.getcwd(), file_),
    #         #           file_,
    #         #            compress_type=zipfile.ZIP_DEFLATED)
    #     except:
    #         pass


    #zip_.close()
