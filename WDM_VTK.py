import vtk
import pandas as pd
import os
import pandas as pd

def main():
    colors = vtk.vtkNamedColors()

    # Wczytanie danych z atlasu
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_name_raw = os.path.join(BASE_DIR, "data", "imaging", "A1_grayT1-1mm_resample.nrrd")
    file_name_seg = os.path.join(BASE_DIR, "data", "labels", "hncma-atlas.nrrd")
    ctbl_path = os.path.join(BASE_DIR, "data", "colortables", "hncma-atlas-lut.ctbl")
    
    tissues_colors = pd.read_table(ctbl_path, comment='#', sep='\\s+')
    
    # Tworzenie mapy kolorów
    label_colors = vtk.vtkLookupTable()
    label_colors.SetNumberOfTableValues(len(tissues_colors))
    label_colors.SetTableRange(0, len(tissues_colors) - 1)
    for i in range(len(tissues_colors)):
        label_colors.SetTableValue(
            i,
            tissues_colors["0.1"][i] / 255,
            tissues_colors["0.2"][i] / 255,
            tissues_colors["0.3"][i] / 255,
            1.0,
        )

    # Tworzenie renderera, okna i interaktora
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    # Wczytanie danych z pliku .nrrd
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(file_name_raw)
    reader.Update()
    raw_data = reader.GetOutput()

    reader_seg = vtk.vtkNrrdReader()
    reader_seg.SetFileName(file_name_seg)
    reader_seg.Update()
    segmentation_data = reader_seg.GetOutput()

    # Wizualizacja danych jako ortogonalnych płaszczyzn
    plane_x = vtk.vtkImagePlaneWidget()
    plane_x.SetInputData(raw_data)
    plane_x.SetPlaneOrientationToXAxes()
    plane_x.SetSliceIndex(raw_data.GetDimensions()[0] // 2)
    plane_x.GetPlaneProperty().SetColor(1, 1, 1)
    plane_x.SetInteractor(interactor)
    plane_x.On()

    plane_y = vtk.vtkImagePlaneWidget()
    plane_y.SetInputData(raw_data)
    plane_y.SetPlaneOrientationToYAxes()
    plane_y.SetSliceIndex(raw_data.GetDimensions()[1] // 2)
    plane_y.GetPlaneProperty().SetColor(1, 1, 1)
    plane_y.SetInteractor(interactor)
    plane_y.On()

    plane_z = vtk.vtkImagePlaneWidget()
    plane_z.SetInputData(raw_data)
    plane_z.SetPlaneOrientationToZAxes()
    plane_z.SetSliceIndex(raw_data.GetDimensions()[2] // 2)
    plane_z.GetPlaneProperty().SetColor(1, 1, 1)
    plane_z.SetInteractor(interactor)
    plane_z.On()

    # Generowanie brył 
    contour_filter = vtk.vtkDiscreteMarchingCubes()
    contour_filter.SetInputData(segmentation_data)
    contour_filter.GenerateValues(len(tissues_colors), 1, len(tissues_colors))
    contour_filter.Update()

    # Tworzenie aktorów dla wybranych segmentów 
    actors = []
    num_segments = len(tissues_colors)
    for segment_id in range(1, num_segments + 1):
        threshold = vtk.vtkThreshold()
        threshold.SetInputConnection(contour_filter.GetOutputPort())
        threshold.SetLowerThreshold(segment_id)
        threshold.SetUpperThreshold(segment_id)
        threshold.Update()

        geometry_filter = vtk.vtkGeometryFilter()
        geometry_filter.SetInputConnection(threshold.GetOutputPort())
        geometry_filter.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(geometry_filter.GetOutputPort())
        mapper.SetLookupTable(label_colors)
        mapper.SetScalarRange(1, num_segments)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetOpacity(1.0)
        renderer.AddActor(actor)
        actors.append(actor)

    '''
    num_segments = len(tissues_colors) 
    actors = []
    for segment_id in range(1, num_segments + 1):
        select_tissue = vtk.vtkImageThreshold()
        select_tissue.SetInputData(segmentation_data)
        select_tissue.ThresholdBetween(segment_id, segment_id)
        select_tissue.SetInValue(255)
        select_tissue.SetOutValue(0)
        select_tissue.Update()
        gaussian = vtk.vtkImageGaussianSmooth()
        gaussian.SetInputConnection(select_tissue.GetOutputPort())
        gaussian.SetStandardDeviations(2.0, 2.0, 2.0)
        gaussian.SetRadiusFactors(1, 1, 1)
        gaussian.Update()
        if gaussian.GetOutput().GetNumberOfCells() > 0:
            iso_surface = vtk.vtkMarchingCubes()
            iso_surface.SetInputConnection(gaussian.GetOutputPort())
            iso_surface.SetValue(0, 127.5)
            iso_surface.Update()
            if iso_surface.GetOutput().GetNumberOfCells() > 0:
                smoother = vtk.vtkWindowedSincPolyDataFilter()
                smoother.SetInputConnection(iso_surface.GetOutputPort())
                smoother.SetNumberOfIterations(20)
                smoother.SetPassBand(0.001)
                smoother.Update()             
                if smoother.GetOutput().GetNumberOfCells() > 0:
                    normals = vtk.vtkPolyDataNormals()
                    normals.SetInputConnection(smoother.GetOutputPort())
                    normals.Update()
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputConnection(normals.GetOutputPort())
                    mapper.SetLookupTable(label_colors)
                    mapper.SetScalarRange(0, num_segments)
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)
                    actor.GetProperty().SetOpacity(1.0)
                    renderer.AddActor(actor)
                    actors.append(actor)
                else:
                    print(f"Brak danych do wygładzenia w {segment_id}")
            else:
                print(f"Brak danych do wygładzenia w {segment_id}")
        else:
            print(f"Brak danych do wygładzenia w {segment_id}")
    '''

    # Przeźroczystości dla danego segmentu
    def create_opacity_callback(actor):
        def update_opacity(slider_widget, event):
            opacity = slider_widget.GetRepresentation().GetValue()
            actor.GetProperty().SetOpacity(opacity)
            render_window.Render()
        return update_opacity

    # Tworzenie suwaków dla wybranych segmentów 
    slider_widgets = []
    for i, actor in enumerate(actors[:5]):
        slider_rep = vtk.vtkSliderRepresentation2D()
        slider_rep.SetMinimumValue(0.0)
        slider_rep.SetMaximumValue(1.0)
        slider_rep.SetValue(1.0)
        slider_rep.SetTitleText(f"Transparency {i+1}")

        slider_rep.GetSliderProperty().SetColor(colors.GetColor3d("Magenta"))
        slider_rep.GetTubeProperty().SetColor(colors.GetColor3d("DarkOrchid"))
        slider_rep.GetCapProperty().SetColor(colors.GetColor3d("Purple"))
        slider_rep.GetSelectedProperty().SetColor(colors.GetColor3d("Thistle"))

        title_property = slider_rep.GetTitleProperty()
        title_property.SetColor(colors.GetColor3d("White"))
        title_property.SetFontSize(10)

        slider_rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        slider_rep.GetPoint1Coordinate().SetValue(0.8, 0.8 - i * 0.15)
        slider_rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        slider_rep.GetPoint2Coordinate().SetValue(0.9, 0.8 - i * 0.15)

        slider_widget = vtk.vtkSliderWidget()
        slider_widget.SetInteractor(interactor)
        slider_widget.SetAnimationModeToAnimate()
        slider_widget.SetRepresentation(slider_rep)
        slider_widget.AddObserver("InteractionEvent", create_opacity_callback(actor))
        slider_widget.EnabledOn()
        slider_widgets.append(slider_widget)

    # Ustawienia kamery i renderera
    renderer.SetBackground(colors.GetColor3d("DimGray"))
    renderer.ResetCamera()

    # Rozpoczęcie interakcji
    render_window.SetSize(800, 600)
    interactor.Initialize()
    render_window.Render()
    interactor.Start()

if __name__ == '__main__':
    main()



