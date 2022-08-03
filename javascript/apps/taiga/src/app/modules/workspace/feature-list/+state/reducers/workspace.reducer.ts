/**
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * Copyright (c) 2021-present Kaleidos Ventures SL
 */

import { createReducer, on, createFeature } from '@ngrx/store';
import { WorkspaceProject, Workspace, Project } from '@taiga/data';
import { immerReducer } from '~/app/shared/utils/store';
import * as WorkspaceActions from '../actions/workspace.actions';

export interface WorkspaceState {
  workspaces: Workspace[];
  loadingWorkspaces: string[];
  creatingWorkspace: boolean;
  loading: boolean;
  createFormHasError: boolean;
  workspaceProjects: Record<Workspace['slug'], WorkspaceProject[]>;
  rejectedInvites: Project['slug'][];
}

export const initialState: WorkspaceState = {
  workspaces: [],
  loadingWorkspaces: [],
  creatingWorkspace: false,
  loading: false,
  createFormHasError: false,
  workspaceProjects: {},
  rejectedInvites: [],
};

export const reducer = createReducer(
  initialState,
  on(WorkspaceActions.fetchWorkspaceList, (state): WorkspaceState => {
    state.loading = true;

    return state;
  }),
  on(
    WorkspaceActions.fetchWorkspaceListSuccess,
    (state, { workspaces }): WorkspaceState => {
      state.workspaces = workspaces;
      state.loading = false;

      state.workspaces.forEach((workspace) => {
        state.workspaceProjects[workspace.slug] = workspace.latestProjects;
      });

      return state;
    }
  ),
  on(WorkspaceActions.createWorkspace, (state): WorkspaceState => {
    state.creatingWorkspace = true;
    state.createFormHasError = false;

    return state;
  }),
  on(
    WorkspaceActions.createWorkspaceSuccess,
    (state, { workspace }): WorkspaceState => {
      state.workspaces = [workspace, ...state.workspaces];
      state.creatingWorkspace = false;

      return state;
    }
  ),
  on(WorkspaceActions.createWorkspaceError, (state): WorkspaceState => {
    state.creatingWorkspace = false;

    return state;
  }),
  on(
    WorkspaceActions.createFormHasError,
    (state, { hasError }): WorkspaceState => {
      state.createFormHasError = hasError;

      return state;
    }
  ),
  on(
    WorkspaceActions.fetchWorkspaceProjects,
    (state, { slug }): WorkspaceState => {
      state.loadingWorkspaces.push(slug);

      return state;
    }
  ),
  on(
    WorkspaceActions.fetchWorkspaceProjectsSuccess,
    (state, { slug, projects }): WorkspaceState => {
      state.workspaceProjects[slug] = projects.map((project) => {
        return {
          name: project.name,
          slug: project.slug,
          description: project.description,
          color: project.color,
          logoSmall: project.logoSmall,
        } as WorkspaceProject;
      });
      state.loadingWorkspaces = [];
      return state;
    }
  ),
  on(WorkspaceActions.resetWorkspace, (state): WorkspaceState => {
    state = {
      ...initialState,
    };

    return state;
  }),
  on(
    WorkspaceActions.setWorkspaceListRejectedInvites,
    (state, { projects }): WorkspaceState => {
      state.rejectedInvites = projects;

      return state;
    }
  )
);

export const workspaceFeature = createFeature({
  name: 'workspaceList',
  reducer: immerReducer(reducer),
});
